# 食物照片記錄 Agent

一個在本機執行的 Discord agent：指定頻道裡有人傳食物照片，就用 `claude -p` 估熱量、記進 Excel、存照片，並回覆上傳者。

設計說明請看 [`docs/architecture.md`](docs/architecture.md)。

## 啟動

先完成 [`docs/discord-server-setup.md`](docs/discord-server-setup.md) 與 [`docs/discord-bot-setup.md`](docs/discord-bot-setup.md)，並把 `.env` 的 `DISCORD_TOKEN`、`CHANNEL_ID` 換成真的值。

```
uv sync
uv run python -m food_agent
```

看到「已上線」就代表成功。關掉終端機（或按 `Ctrl+C`）agent 就停止，期間傳的照片不會被補處理。

跑測試（不需要 Discord、不會呼叫 Claude）：

```
uv run python -m pytest -q
```

## 使用方式

- 在指定頻道傳食物照片：照片上會先出現 ⏳；處理完變成 ✅（失敗是 ❌），並回覆結果與「當日已攝取熱量」。
- 失敗（包含不是圖片、檔案太大、claude 分析不出來）：回覆「分析失敗，請再傳一次」。
- 傳含「今日熱量」的文字：列出今天整個頻道每一餐與總計。

## 設定（`.env`）

| 項目 | 意思 |
|---|---|
| `DISCORD_TOKEN` | bot 的密碼。**不能公開、不能 commit** |
| `CHANNEL_ID` | 只聽這個頻道 |
| `CLAUDE_MODEL` | `claude -p` 用的模型 |
| `DATA_DIR` | 資料資料夾（相對路徑以專案資料夾為準）。裡面有 `photos/`、`records/food_log.xlsx`、`inbox/`（暫存） |

`.env` 與 `data/`、`photos/`、`records/`、`inbox/`、`*.xlsx` 都已在 `.gitignore`。

## 四段安全防護

全部在 `src/food_agent/guards.py`，一開始**全部開啟**。每一段都用下面這種註解標出開始與結束，要關掉就把中間整段註解掉：

```python
# ==== 防護 N：說明　開始 ====
...
# ==== 防護 N 結束 ====
```

| 防護 | 做什麼 | 位置（約） |
|---|---|---|
| 防護 1 | `claude -p` 只能碰到「只有這一張待分析照片」的暫存資料夾；只開放讀檔工具；不傳 Discord 相關環境變數 | `guards.py` 第 38～46 行 |
| 防護 2 | 上傳者打的字只當資料，絕不接進給 `claude -p` 的指令 | `guards.py` 第 61～63 行 |
| 防護 3 | 食物名稱拿去當檔名前，清掉 `/ \ ..` 冒號等字，並確認檔案真的落在 `photos/` 裡 | `guards.py` 第 95～101 行 |
| 防護 4 | 寫進 Excel 的文字若以 `= + - @` 開頭，補單引號並設為純文字 | `guards.py` 第 114～118 行 |

行號會隨編輯變動，可用這行重查：`grep -n "==== 防護" src/food_agent/guards.py`

## 程式結構

```
src/food_agent/
├─ app.py        啟動入口、啟動時的錯誤說明
├─ config.py     讀 .env、自我檢查、各種上限
├─ bot.py        Discord 事件：只聽 CHANNEL_ID，分流給照片或「今日熱量」
├─ worker.py     佇列與單一作業員（一次只開一個 claude -p）、每人上限、回覆
├─ analyzer.py   呼叫 claude -p、解析並檢查 JSON
├─ storage.py    存照片、寫 Excel（只加不改）、算當日累計
├─ guards.py     四段防護
└─ replies.py    所有回覆文字
tests/           自動測試
```
