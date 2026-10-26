"""四段安全防護（詳見 docs/architecture.md 第 12 節）。

每一段都用下面這種註解標出開始與結束，一開始全部開啟：

    # ==== 防護 N：說明　開始 ====
    ...
    # ==== 防護 N 結束 ====

教學時要關掉某一段，只要把「開始」到「結束」之間整段註解掉即可。
函式在區塊外面都先寫好「不防護時的預設行為」，所以整段註解掉之後程式仍能執行，
只是少了那一層保護。四段彼此獨立，關掉其中一段不會影響其他段。

各段位置（行號會隨編輯變動，以下指令可隨時重查）：
    grep -n "==== 防護" src/food_agent/guards.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# 防護 1：claude -p 的檔案範圍隔離
# ---------------------------------------------------------------------------
def apply_claude_isolation(
    args: list[str],
    env: dict[str, str],
    job_dir: Path,
    data_dir: Path,
) -> tuple[list[str], dict[str, str], Path]:
    """決定 claude -p 的額外旗標、環境變數與工作資料夾。

    不防護時：工作資料夾是整個 DATA_DIR，claude 看得到所有人的照片與紀錄。
    """
    cwd = data_dir
    # ==== 防護 1：claude -p 的檔案範圍隔離　開始 ====
    # 1) 工作資料夾只有「這一張待分析照片」，處理完整個刪除
    cwd = job_dir
    # 2) --restricted：把檔案工具限制在工作資料夾內，拿掉執行指令類工具，忽略使用者的設定檔
    # 3) --tools Read：只有「讀檔」一種工具；--strict-mcp-config：不載入任何外掛伺服器
    args = args + ["--restricted", "--tools", "Read", "--strict-mcp-config", "--disable-slash-commands"]
    # 4) 不把 Discord 相關的環境變數（例如 token）交給子程序
    env = {key: value for key, value in env.items() if "DISCORD" not in key.upper()}
    # ==== 防護 1 結束 ====
    return args, env, cwd


# ---------------------------------------------------------------------------
# 防護 2：上傳者打的字只能當資料，不能接進給 claude -p 的指令
# ---------------------------------------------------------------------------
def compose_prompt(base_prompt: str, uploader_text: str) -> str:
    """組出最後送給 claude -p 的指示文字。

    不防護時：上傳者打的字會被直接接在指示後面，等於讓陌生人改寫指令。
    """
    prompt = base_prompt
    if uploader_text:
        prompt = f"{base_prompt}\n\n上傳者的附註：{uploader_text}"
    # ==== 防護 2：上傳者的字只當資料，絕不接進指令　開始 ====
    prompt = base_prompt  # 指示文字永遠只有程式寫死的那一份；上傳者的字在這裡被丟掉
    # ==== 防護 2 結束 ====
    return prompt


# ---------------------------------------------------------------------------
# 防護 3：食物名稱當檔名前先清洗
# ---------------------------------------------------------------------------
_FORBIDDEN_FILENAME_CHARS = re.compile(r'[\x00-\x1f\x7f/\\:*?"<>|]')
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
MAX_NAME_LENGTH = 20


def _clean_filename_part(name: str) -> str:
    cleaned = _FORBIDDEN_FILENAME_CHARS.sub("", name)
    cleaned = cleaned.replace("..", "")
    cleaned = cleaned.strip(" .")[:MAX_NAME_LENGTH].strip(" .")
    if not cleaned or cleaned.split(".")[0].upper() in _WINDOWS_RESERVED:
        cleaned = "food"
    return cleaned


def build_photo_path(photos_dir: Path, stamp: str, name: str, attempt: int = 1) -> Path:
    """組出照片的完整路徑：<photos_dir>/<stamp> <名稱簡稱>[-N].jpg

    不防護時：名稱原樣放進檔名，名稱裡的 ../ 之類的字可以讓檔案跑到別的資料夾。
    """
    suffix = "" if attempt == 1 else f"-{attempt}"
    path = photos_dir / f"{stamp} {name}{suffix}.jpg"
    # ==== 防護 3：食物名稱當檔名前先清洗　開始 ====
    safe_name = _clean_filename_part(name)
    path = photos_dir / f"{stamp} {safe_name}{suffix}.jpg"
    # 最後再確認：這個路徑真的就在 photos_dir 裡面，不是的話直接拒絕
    if path.resolve().parent != photos_dir.resolve():
        raise ValueError("照片路徑跑出 photos 資料夾，已拒絕")
    # ==== 防護 3 結束 ====
    return path


# ---------------------------------------------------------------------------
# 防護 4：Excel 公式注入
# ---------------------------------------------------------------------------
def write_text_cell(cell, value: str) -> None:
    """把一段「來自外部的文字」寫進 Excel 儲存格。

    不防護時：以 = 開頭的文字會被 openpyxl 當成公式，用 Excel 打開就會被執行。
    """
    cell.value = value
    # ==== 防護 4：Excel 公式注入　開始 ====
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        cell.value = "'" + value  # 前面補單引號，Excel 就會當成純文字顯示
    cell.data_type = "s"          # 明確指定這格是「文字」，不讓 openpyxl 自己猜成公式
    # ==== 防護 4 結束 ====


def scrubbed_environ() -> dict[str, str]:
    """目前的環境變數副本（防護 1 會再從裡面拿掉 Discord 相關的項目）。"""
    return dict(os.environ)
