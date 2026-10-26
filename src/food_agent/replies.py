"""所有回覆文字的組裝。

模型回傳的名稱與成份是外面來的內容，放進回覆前一律先跳脫 Discord 的 @ 與格式符號。
"""

from __future__ import annotations

from datetime import date

import discord

from .analyzer import Analysis
from .storage import Meal

PROCESSING_EMOJI = "⏳"
DONE_EMOJI = "✅"
FAILED_EMOJI = "❌"
FAILURE_TEXT = "分析失敗，請再傳一次"
DISCORD_LIMIT = 1900  # Discord 單則訊息上限 2000 字，留一點餘裕


def _safe(text: str) -> str:
    return discord.utils.escape_markdown(discord.utils.escape_mentions(text))


def _clip(text: str) -> str:
    return text if len(text) <= DISCORD_LIMIT else text[: DISCORD_LIMIT - 1] + "…"


def _day_label(day: date) -> str:
    return day.strftime("%Y/%m/%d")


def format_result(analysis: Analysis, day: date, day_total_kcal: int) -> str:
    if analysis.is_food:
        lines = [f"✅ 是食物：{_safe(analysis.name)}", "成份："]
        for item in analysis.ingredients:
            lines.append(f"・{_safe(item.name)}　約 {item.weight_g} g　約 {item.kcal} 大卡")
        lines.append(f"整餐：約 {analysis.total_weight_g} g　約 {analysis.total_kcal} 大卡")
    else:
        lines = [
            "🚫 不是食物",
            f"成份：{_safe(analysis.name)}",
            "重量：—　熱量：—",
        ]
    lines.append(f"當日已攝取熱量（{_day_label(day)}）：約 {day_total_kcal} 大卡")
    return _clip("\n".join(lines))


def format_failure() -> str:
    return FAILURE_TEXT


def format_daily_query(day: date, meals: list[Meal]) -> str:
    if not meals:
        return f"{_day_label(day)} 還沒有記錄任何一餐"

    total = sum(meal.kcal or 0 for meal in meals)
    footer = f"{_day_label(day)} 總共約 {total} 大卡"

    lines = []
    for meal in meals:
        kcal = f"約 {meal.kcal} 大卡" if meal.kcal is not None else "—"
        lines.append(f"{meal.when:%H:%M}　{_safe(meal.uploader)}　{_safe(meal.description)}　{kcal}")

    # 太長就只留最近的幾餐，總計仍是全部
    budget = DISCORD_LIMIT - len(footer) - 40
    kept: list[str] = []
    used = 0
    for line in reversed(lines):
        if used + len(line) + 1 > budget:
            break
        kept.append(line)
        used += len(line) + 1
    kept.reverse()
    header = f"{_day_label(day)} 的紀錄"
    if len(kept) < len(lines):
        header += f"（只顯示最近 {len(kept)} 餐，共 {len(lines)} 餐）"
    return "\n".join([header, *kept, footer])
