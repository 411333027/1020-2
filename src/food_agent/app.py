"""啟動入口：讀設定、自我檢查、連上 Discord。"""

from __future__ import annotations

import logging
import sys

import discord

from .bot import FoodClient
from .config import ConfigError, load_config


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("food_agent")

    try:
        config = load_config()
    except ConfigError as exc:
        log.error("設定有問題，無法啟動：%s", exc)
        sys.exit(1)

    log.info("DATA_DIR = %s，模型 = %s", config.data_dir, config.claude_model)

    client = FoodClient(config)
    try:
        client.run(config.discord_token, log_handler=None)  # 日誌格式用上面自己設定的；token 不會被印出
    except discord.LoginFailure:
        log.error("登入失敗：DISCORD_TOKEN 不正確（可能貼錯、多了空格，或已被 Reset）。")
        sys.exit(1)
    except discord.PrivilegedIntentsRequired:
        log.error(
            "Developer Portal 還沒打開 Message Content Intent。"
            "請到 Bot 頁面打開並按 Save Changes（見 docs/discord-bot-setup.md 第二節）。"
        )
        sys.exit(1)
