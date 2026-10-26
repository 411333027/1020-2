"""讀取 .env 設定，並在啟動時做自我檢查。"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 這些是可調整的上限（見 docs/architecture.md 第 7、13 節）
MAX_IMAGE_BYTES = 10 * 1024 * 1024      # 單張圖片上限 10 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_QUEUE_SIZE = 20                     # 整個佇列最多排幾張
MAX_PENDING_PER_USER = 3                # 同一人同時最多排幾張
MAX_PHOTOS_PER_USER_PER_DAY = 30        # 每人每日最多處理幾張
CLAUDE_TIMEOUT_SECONDS = 120            # 單次 claude -p 最多等幾秒
EXCEL_RETRY_SECONDS = 5                 # Excel 被鎖住時，每隔幾秒重試
EXCEL_MAX_RETRIES = 12                  # 最多重試幾次（約一分鐘）

QUERY_KEYWORD = "今日熱量"


class ConfigError(Exception):
    """設定有問題。訊息會直接顯示給使用者看，所以要寫白話。"""


@dataclass(frozen=True)
class Config:
    discord_token: str
    channel_id: int
    claude_model: str
    data_dir: Path
    claude_bin: str

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"

    @property
    def records_dir(self) -> Path:
        return self.data_dir / "records"

    @property
    def inbox_dir(self) -> Path:
        return self.data_dir / "inbox"

    @property
    def excel_path(self) -> Path:
        return self.records_dir / "food_log.xlsx"


def load_config() -> Config:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        raise ConfigError(f"找不到設定檔 {env_path}。請先建立 .env（見 docs/discord-bot-setup.md）。")

    # 只讀進這個 dict，不放進 os.environ，這樣 token 不會被子程序繼承
    values = dotenv_values(env_path)

    def need(key: str) -> str:
        value = (values.get(key) or "").strip()
        if not value:
            raise ConfigError(f".env 裡的 {key} 是空的，請填上。")
        return value

    token = need("DISCORD_TOKEN")
    if token == "你的bot_token":
        raise ConfigError(".env 的 DISCORD_TOKEN 還是範例文字，請換成真的 bot token。")

    channel_text = need("CHANNEL_ID")
    if not channel_text.isdigit():
        raise ConfigError(".env 的 CHANNEL_ID 必須是一串數字（請見 docs/discord-server-setup.md）。")

    model = need("CLAUDE_MODEL")

    data_dir = Path(need("DATA_DIR")).expanduser()
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    data_dir = data_dir.resolve()

    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise ConfigError("找不到 claude 指令。請先安裝 Claude Code 並登入。")

    config = Config(token, int(channel_text), model, data_dir, claude_bin)

    try:
        for folder in (config.photos_dir, config.records_dir, config.inbox_dir):
            folder.mkdir(parents=True, exist_ok=True)
        probe = config.data_dir / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise ConfigError(f"DATA_DIR（{config.data_dir}）不能寫入：{exc}") from exc

    return config
