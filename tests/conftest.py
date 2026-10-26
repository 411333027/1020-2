import io
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from food_agent.config import Config


@pytest.fixture
def config(tmp_path: Path) -> Config:
    cfg = Config("token", 1, "haiku", tmp_path, "claude")
    for folder in (cfg.photos_dir, cfg.records_dir, cfg.inbox_dir):
        folder.mkdir(parents=True)
    return cfg


@pytest.fixture
def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, "PNG")
    return buffer.getvalue()


@pytest.fixture
def when() -> datetime:
    return datetime(2026, 10, 26, 12, 34, 56)
