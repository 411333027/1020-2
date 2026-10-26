"""佇列與單一作業員：照片一張一張排隊處理，同一時間只會有一個 claude -p。"""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime

import discord

from . import replies, storage
from .analyzer import AnalysisError, analyze_photo
from .config import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_BYTES,
    MAX_PENDING_PER_USER,
    MAX_PHOTOS_PER_USER_PER_DAY,
    MAX_QUEUE_SIZE,
    Config,
)

log = logging.getLogger("food_agent.worker")


@dataclass(frozen=True)
class Job:
    message: discord.Message
    attachment: discord.Attachment


async def reply_to(message: discord.Message, text: str) -> None:
    """用「回覆該則訊息」的方式回在頻道裡（會通知上傳者）。原訊息被刪掉時改成直接在頻道 @ 他。"""
    try:
        await message.reply(text, mention_author=True)
    except discord.HTTPException:
        try:
            await message.channel.send(
                f"{message.author.mention} {text}",
                allowed_mentions=discord.AllowedMentions(users=[message.author]),
            )
        except discord.HTTPException:
            log.exception("回覆失敗")


class PhotoWorker:
    def __init__(self, config: Config, bot_user: discord.abc.Snowflake) -> None:
        self.config = config
        self.bot_user = bot_user
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self.pending: Counter[int] = Counter()
        self.daily: Counter[tuple[date, int]] = Counter()
        # Excel 同一時間只准一個人讀寫（作業員、查詢都要拿這把鎖）
        self.excel_lock = asyncio.Lock()

    # ---- 收件 ----------------------------------------------------------
    def rejection_reason(self, user_id: int) -> str | None:
        """超出限制時回傳原因（只寫在終端機日誌，不給上傳者看）。"""
        if self.queue.qsize() >= MAX_QUEUE_SIZE:
            return f"佇列已滿（{MAX_QUEUE_SIZE} 張）"
        if self.pending[user_id] >= MAX_PENDING_PER_USER:
            return f"同一人排隊中已有 {MAX_PENDING_PER_USER} 張"
        today = date.today()
        if self.daily[(today, user_id)] >= MAX_PHOTOS_PER_USER_PER_DAY:
            return f"今日已達每人上限 {MAX_PHOTOS_PER_USER_PER_DAY} 張"
        return None

    async def submit(self, message: discord.Message, attachment: discord.Attachment) -> bool:
        """收下一張照片。成功排進佇列回傳 True；被拒絕時已回覆失敗訊息並回傳 False。"""
        user_id = message.author.id

        problem = None
        if attachment.content_type is None or attachment.content_type.split(";")[0] not in ALLOWED_IMAGE_TYPES:
            problem = f"不支援的圖片格式：{attachment.content_type}"
        elif attachment.size > MAX_IMAGE_BYTES:
            problem = f"圖片太大：{attachment.size} bytes"
        else:
            problem = self.rejection_reason(user_id)

        if problem:
            log.warning("拒絕 %s 的照片：%s", message.author, problem)
            await self._finish(message, replies.format_failure(), ok=False)
            return False

        self.pending[user_id] += 1
        self.daily[(date.today(), user_id)] += 1
        await self._add_reaction(message, replies.PROCESSING_EMOJI)
        await self.queue.put(Job(message, attachment))
        log.info("已排隊：%s 的照片（佇列長度 %d）", message.author, self.queue.qsize())
        return True

    # ---- 作業員 --------------------------------------------------------
    async def run(self) -> None:
        """永遠不結束的迴圈：一次拿一張來處理。任何錯誤都只會讓那一張失敗。"""
        while True:
            job = await self.queue.get()
            try:
                await self._process(job)
            except Exception:  # noqa: BLE001 - 作業員絕對不能死
                log.exception("處理照片時發生未預期的錯誤")
                await self._finish(job.message, replies.format_failure(), ok=False)
            finally:
                self.pending[job.message.author.id] -= 1
                self.queue.task_done()

    async def _process(self, job: Job) -> None:
        config = self.config
        message, attachment = job.message, job.attachment
        job_dir = config.inbox_dir / uuid.uuid4().hex
        try:
            job_dir.mkdir(parents=True)

            data = await attachment.read()
            if len(data) > MAX_IMAGE_BYTES:
                raise storage.StorageError("下載後圖片超過大小上限")
            await asyncio.to_thread(storage.validate_image, data)

            extension = ALLOWED_IMAGE_TYPES[attachment.content_type.split(";")[0]]
            photo_path = job_dir / f"photo.{extension}"
            photo_path.write_bytes(data)

            # 上傳者打的字（message.content）在這裡傳進去，但防護 2 會把它丟掉
            analysis = await analyze_photo(config, photo_path, job_dir, message.content)

            when = message.created_at.astimezone().replace(tzinfo=None)  # 電腦的本地時間
            uploader = message.author.display_name
            photo_name = analysis.name if analysis.is_food else storage.NOT_FOOD_LABEL

            def record() -> int:
                saved = storage.save_photo(config, data, when, photo_name)
                try:
                    return storage.append_record(config, when, uploader, analysis, saved)
                except Exception:
                    saved.unlink(missing_ok=True)  # Excel 寫不進去就不留孤兒照片
                    raise

            async with self.excel_lock:
                day_total = await asyncio.to_thread(record)

            await self._finish(message, replies.format_result(analysis, when.date(), day_total), ok=True)
        except (AnalysisError, storage.StorageError) as exc:
            log.warning("%s 的照片處理失敗：%s", message.author, exc)
            await self._finish(message, replies.format_failure(), ok=False)
        finally:
            shutil.rmtree(job_dir, ignore_errors=True)

    # ---- Discord 小工具 --------------------------------------------------
    async def _add_reaction(self, message: discord.Message, emoji: str) -> None:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException as exc:
            log.warning("無法加上 %s 反應（機器人可能缺少「新增反應」權限）：%s", emoji, exc)

    async def _finish(self, message: discord.Message, text: str, *, ok: bool) -> None:
        try:
            await message.remove_reaction(replies.PROCESSING_EMOJI, self.bot_user)
        except discord.HTTPException:
            pass
        await self._add_reaction(message, replies.DONE_EMOJI if ok else replies.FAILED_EMOJI)
        await reply_to(message, text)

    async def query_today(self) -> str:
        """「今日熱量」查詢：列出今天整個頻道的每一餐與總計。"""
        today = datetime.now().date()
        async with self.excel_lock:
            meals = await asyncio.to_thread(storage.meals_on, self.config, today)
        return replies.format_daily_query(today, meals)
