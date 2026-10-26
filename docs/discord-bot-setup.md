# Discord Bot 設定步驟

這份文件帶你做四件事：

1. 在 Discord Developer Portal 建立 application 和 bot
2. 打開 Message Content Intent
3. 拿到 bot token，並安全地存起來
4. 設定權限，把 bot 邀進你自己的 Server

**開始前**：請先完成 `docs/discord-server-setup.md`（你要先有自己的 Server）。
**你的電腦是 Windows。** 全部步驟都在瀏覽器裡做，不用安裝東西。

> Developer Portal 偶爾會改版，按鈕位置或文字可能略有不同。文件裡中文後面附上英文名稱供對照；Portal 本身通常是英文介面，請以英文為準。

**名詞先講一下**

- **Developer Portal（開發者後台）**：Discord 讓你建立機器人的網站。
- **application**：你在 Discord 登記的一個「應用程式」。bot 是它底下的一個機器人帳號。
- **bot**：以程式身分登入 Discord 的「假帳號」，可以讀頻道訊息、發訊息。我們的 agent 就是透過它跟 Discord 說話。
- **token**：bot 的**密碼**。知道 token 的人，就能完全控制你的 bot。

---

## ⚠️ 最重要的事：bot token 的規則

> ### 🚫 bot token 絕對不能：
> - **貼給任何人**（同學、朋友、老師、網路論壇都不行）
> - **貼進這個對話**（包含和 Claude 的任何對話視窗）
> - **commit 進 git**（也不能推到 GitHub）
> - **放進截圖、錄影、日誌、文件裡**
>
> ### ✅ token 只能放在一個地方：
> 你電腦上專案資料夾裡的 `.env` 檔案（這個檔案已經設定成 git 不會追蹤）。
>
> ### 為什麼這麼嚴格？
> 拿到 token 的人可以冒充你的 bot：在你的 Server 發任何訊息、讀取頻道內容。就算你事後刪掉貼文，別人可能已經複製走。Discord 和 GitHub 的自動掃描程式也會抓出外洩的 token，並直接把它作廢。
>
> ### 如果不小心貼出去了：
> 立刻回到 Developer Portal 的 Bot 頁面按 **Reset Token**（見第三節），舊的馬上失效，然後把新的存進 `.env`。**不要猶豫、不要先看有沒有人看到。**

之後需要幫忙除錯時，請告訴別人「token 有設定」就好，**不要貼 token 內容**。

---

## 一、建立 application 和 bot

1. 打開瀏覽器，進入 `https://discord.com/developers/applications`。
2. 用你的 Discord 帳號登入（如果問你要不要授權，按同意）。
3. 看畫面**右上角**，按藍色的 **「New Application」**。
4. 在「Name」欄位輸入名字，例如 `食物記錄 bot`。
   - 這個名字等一下會是 bot 在頻道裡顯示的名稱。
5. 勾選同意 Discord 的開發者條款（Developer Terms of Service）。
6. 按 **「Create」**。

你會進入這個 application 的設定頁。看畫面**左邊**有一排選單：General Information、Installation、OAuth2、Bot……。

7. 按左邊選單的 **「Bot」**。
   - 新建的 application 預設就已經有 bot 帳號，不需要另外按「Add Bot」。
8. 這個頁面往下捲，找到 **「Public Bot」** 的開關，把它**關掉**（灰色）。
   - 原因：關掉之後，只有你自己能把這個 bot 邀進 Server，別人拿到邀請連結也加不了。
   - 如果頁面要你按「Save Changes」，就按。

---

## 二、打開 Message Content Intent（一定要做）

**Intent（意圖）**：Discord 要求 bot 事先「申報」自己要收哪一類資料。有些資料比較敏感，必須你親手打開開關，bot 才收得到。

**為什麼我們一定要打開 Message Content Intent**

- 沒打開的話，bot 看得到「有人發了訊息」，但**看不到訊息的內容**：包含文字，也包含附件（照片）。
- 我們的 agent 需要它做兩件事：
  1. 判斷訊息有沒有附照片，並下載照片。
  2. 判斷訊息文字有沒有包含「今日熱量」。
- 沒打開的後果：程式啟動時會直接失敗（錯誤訊息裡有 `PrivilegedIntentsRequired`），或是 bot 在線上卻對照片完全沒反應。

**步驟**

1. 還在左邊選單的 **「Bot」** 頁面。
2. 往下捲到 **「Privileged Gateway Intents」** 這一區。
3. 找到 **「Message Content Intent」**，把右邊的開關**打開**（變成藍色／綠色）。
4. 另外兩個（Presence Intent、Server Members Intent）**保持關閉**，我們用不到。
5. 頁面最下面會跳出一條提示，按 **「Save Changes」**。
   - 沒按儲存，開關會被還原。

> 你的 bot 只在少於 100 個 Server 時，這個開關自己打開就可以用，不需要申請審核。我們的使用情境完全符合。

---

## 三、取得 bot token

1. 還在左邊選單的 **「Bot」** 頁面，往上捲到 **「Token」** 區塊。
2. 按 **「Reset Token」**。
   - 如果跳出確認視窗，按 **「Yes, do it!」**。
   - Discord 可能會要你輸入密碼或兩步驟驗證碼，照做。
3. 畫面會出現一長串文字，這就是 **bot token**。
   - **這串只會顯示一次**，離開這個頁面就看不到了。
4. 按 **「Copy」**。

### 把 token 存進 `.env`（只能存這一個地方）

1. 打開檔案總管，進入專案資料夾 `C:\Users\Grace\1020-2`。
2. 用「記事本」（Notepad）建立一個新檔案，內容這樣寫（四行，值要換成你自己的）：

   ```
   DISCORD_TOKEN=貼上剛剛複製的 token
   CHANNEL_ID=貼上你在 server 設定文件拿到的頻道編號
   CLAUDE_MODEL=claude-sonnet-5-5
   DATA_DIR=C:\Users\Grace\food-data
   ```

   - `=` 前後**不要有空格**。
   - token 不用加引號。
3. 按 `Ctrl + S` 存檔。在「另存新檔」視窗：
   - 「檔案名稱」輸入 `.env`（前面有一個點）。
   - **「存檔類型」務必選「所有檔案 (*.*)」**，否則記事本會偷偷存成 `.env.txt`，程式讀不到。
   - 存檔位置是 `C:\Users\Grace\1020-2`。
4. 關掉記事本。

### 確認 `.env` 不會被 commit

1. 在專案資料夾空白處按 **Shift + 右鍵**，選「在此處開啟 PowerShell 視窗」（或「在終端機中開啟」）。
2. 輸入下面指令後按 Enter：

   ```
   git status
   ```

3. 看輸出的清單：**裡面不應該出現 `.env`**。
   - 沒出現 ✅ 代表 git 已經忽略它，安全。
   - 出現了 ❌ 先不要 commit，立刻停下來把問題告訴協助你的人（不要貼 `.env` 的內容）。

---

## 四、設定權限，並把 bot 邀進你的 Server

### 要給哪些權限？（最小權限原則）

只給 bot **做事必須用到**的權限，不給管理員：

| 權限（英文） | 中文 | 為什麼需要 |
|---|---|---|
| View Channels | 檢視頻道 | 才看得到頻道裡的訊息 |
| Send Messages | 發送訊息 | 才能回「處理中」和結果 |
| Read Message History | 讀取訊息歷史 | 才能「回覆」某則照片訊息 |
| Add Reactions | 新增反應 | 才能在照片上加 ⏳（排隊中）、✅（完成）、❌（失敗） |

**不要勾**：Administrator（管理員）、Manage Messages、Mention Everyone、Manage Channels 等其他所有項目。

### 步驟：產生邀請網址

1. 回到 Developer Portal，按左邊選單的 **「OAuth2」**。
2. 往下捲到 **「OAuth2 URL Generator」**（網址產生器）區塊。
3. 在 **「Scopes」**（範圍）區塊，勾選 **`bot`**。
   - 只勾這一個。
4. 勾了 `bot` 之後，下面會出現 **「Bot Permissions」**（機器人權限）區塊。勾選這四項：
   - **View Channels**（可能在「General Permissions」底下）
   - **Send Messages**（在「Text Permissions」底下）
   - **Read Message History**（在「Text Permissions」底下）
   - **Add Reactions**（在「Text Permissions」底下）
5. 如果有 **「Integration Type」**，選 **「Guild Install」**。
6. 捲到最下面，會看到 **「Generated URL」**，按 **「Copy」** 複製。
   - 這個邀請網址**不是密碼**，可以安心使用；它只是「把這個 bot 加進 Server 的入口」。

### 步驟：把 bot 加進你的 Server

1. 打開新的瀏覽器分頁，貼上剛複製的網址，按 Enter。
2. 在「新增至伺服器」（Add to Server）下拉選單，選你的 `食物記錄` Server。
   - 選單裡只會列出**你有管理權限**的 Server。看不到的話，確認你登入的是建立 Server 的那個帳號。
3. 按 **「繼續」**（Continue）。
4. 確認畫面會列出你剛選的四項權限，檢查**沒有多勾**，然後按 **「授權」**（Authorize）。
5. 如果出現「我是人類」的驗證，照著做。

### 確認 bot 已經加入

1. 回到 Discord，進入你的 `食物記錄` Server。
2. 看右邊的成員清單，會多一個帶有 **「APP」** 小標籤的成員，名稱是你取的 bot 名字。
3. 此時它顯示為**離線**（灰色），這是正常的：agent 程式還沒啟動。程式開起來之後，它才會變成在線上（綠色）。

### 選做：讓 bot 只能碰 `食物記錄` 頻道

即使不做這步，agent 程式本身也只會聽 `CHANNEL_ID` 那個頻道。但如果你想在 Discord 這邊也限制：

1. 對 `食物記錄` 頻道按右鍵 →「編輯頻道」。
2. 左邊選「權限」（Permissions）。
3. 在「進階權限」下，按 **「＋」** 新增你的 bot，再依上表給四項權限。
4. 回到 Server 的其他頻道，把 bot 的權限取消（或不給）。

---

## 完成檢查表

- [ ] 我在 Developer Portal 建立了 application，Public Bot 已關閉
- [ ] **Message Content Intent 已打開並按了 Save Changes**
- [ ] 我已取得 bot token，並**只**存在 `.env` 裡
- [ ] `.env` 的檔名正確（不是 `.env.txt`），且 `git status` 看不到它
- [ ] 我沒有把 token 貼給任何人、也沒有貼進任何對話或文件
- [ ] 我只給 bot 四項權限：View Channels、Send Messages、Read Message History、Add Reactions
- [ ] bot 已出現在我的 Server 成員清單（顯示離線是正常的）

## 常見問題

| 狀況 | 可能原因 | 怎麼辦 |
|---|---|---|
| 程式啟動時出現 `PrivilegedIntentsRequired` | Message Content Intent 沒開，或開了沒按 Save | 回第二節，打開後一定要按 Save Changes |
| 程式啟動出現 `LoginFailure` / `Improper token` | token 貼錯、多了空格或引號、已被 Reset | 回第三節重新 Reset Token，重新貼到 `.env` |
| bot 在線上，但傳照片完全沒反應 | `CHANNEL_ID` 錯誤、傳在別的頻道、bot 沒有該頻道權限 | 檢查 `CHANNEL_ID`；確認 bot 在 `食物記錄` 頻道有 View Channels 與 Send Messages |
| 邀請網址打開後，下拉選單看不到我的 Server | 登入錯帳號，或你在那個 Server 沒有管理權限 | 換成建立 Server 的帳號 |
| 邀請時出現「需要程式碼授權」之類的錯誤 | 勾了多餘的 scope（例如 `applications.commands` 以外的授權碼流程） | 回第四節，Scopes 只勾 `bot` |
| 忘記 token | token 只顯示一次 | 回第三節再按一次 Reset Token，取得新的並更新 `.env`（舊的會失效） |
