"""Discord 端：用 Gateway 連線收訊息，分流給照片流程或「今日熱量」查詢。"""

from __future__ import annotations

import logging
import shutil

import discord

from .config import QUERY_KEYWORD, Config
from .worker import PhotoWorker, reply_to

log = logging.getLogger("food_agent.bot")


class FoodClient(discord.Client):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # 要在 Developer Portal 打開 Message Content Intent
        # 預設誰都不 @：避免模型或名稱裡的 @everyone 真的通知全伺服器。
        # 「回覆」時通知被回覆的人（replied_user）是我們要的。
        super().__init__(
            intents=intents,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=True),
        )
        self.config = config
        self.worker: PhotoWorker | None = None

    async def setup_hook(self) -> None:
        # 上次當機可能留下沒清掉的暫存資料夾
        for leftover in self.config.inbox_dir.iterdir():
            shutil.rmtree(leftover, ignore_errors=True)

    async def on_ready(self) -> None:
        if self.worker is None:
            self.worker = PhotoWorker(self.config, self.user)
            self.loop.create_task(self.worker.run())
        channel = self.get_channel(self.config.channel_id)
        if channel is None:
            log.error("看不到 CHANNEL_ID=%s 這個頻道：請確認編號正確，且機器人有「檢視頻道」權限", self.config.channel_id)
        else:
            log.info("已上線：%s，只聽頻道 #%s", self.user, getattr(channel, "name", "?"))

    async def on_message(self, message: discord.Message) -> None:
        # 只聽指定的那一個頻道；機器人（含自己）的訊息一律不理
        if message.channel.id != self.config.channel_id or message.author.bot:
            return
        if self.worker is None:
            return

        images = [a for a in message.attachments if (a.content_type or "").startswith("image/")]

        if images:
            for attachment in images:
                await self.worker.submit(message, attachment)
            return

        # 沒有圖片：只有訊息裡含「今日熱量」才有反應，其他一律不理
        if QUERY_KEYWORD in message.content:
            try:
                text = await self.worker.query_today()
            except Exception:  # noqa: BLE001
                log.exception("查詢今日熱量失敗")
                text = "查詢失敗，請稍後再試"
            await reply_to(message, text)
