# CLAUDE.md

一個在本機執行的 Discord agent：頻道裡有人傳食物照片，就用 `claude -p` 估熱量、記進 Excel、存照片，並回覆上傳者。

## 開始任何工作前

先讀 `docs/architecture.md`。設計決定以它為準；它與 `docs/requirements (3).md` 不同之處，以 architecture.md 第 0 節為準。

## 四段防護

架構文件第 12 節的四段防護（防護 1～4）：

- 各自集中成一小段，放在 `guards.py`。
- 各自用清楚的註解標起來，格式固定：

  ```python
  # ===== 防護 N 開始：說明 =====
  ...
  # ===== 防護 N 結束 =====
  ```

- **一開始全部開啟。** 之後教學才會逐段關掉做對照，所以四段要彼此獨立，關掉一段不能影響其他段。
- 不要把防護邏輯散落到別的檔案，也不要刪掉或改掉開始 / 結束標記。

## 不可以 commit 的東西

- 不可以把 `.env` commit 進 git（裡面有 `DISCORD_TOKEN`）。只提交 `.env.example`（假的值）。
- `DATA_DIR` 裡的照片和 Excel（`photos/`、`records/`、`inbox/`、`*.xlsx`）也不要 commit。
- 不要把 token 貼進日誌、回覆、文件或 commit message。
