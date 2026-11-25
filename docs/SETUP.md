# Hướng dẫn thiết lập (SETUP)

Bot cần 2 nguồn cấu hình: **Telegram** (bot + chat nhận cảnh báo) và **Threads** (Meta app + access token). Làm theo thứ tự dưới đây.

## Mục lục

- [A. Telegram](#a-telegram)
- [B. Threads (Meta)](#b-threads-meta)
- [C. Cấu hình `.env` và chạy bot](#c-cấu-hình-env-và-chạy-bot)
- [D. Test thử pipeline](#d-test-thử-pipeline)
- [E. Bảo trì token](#e-bảo-trì-token)

---

## A. Telegram

### A1. Tạo bot

1. Mở Telegram, tìm **@BotFather**, gửi `/newbot`.
2. Đặt tên hiển thị (VD `Threads Alert Bot`) và username kết thúc bằng `bot` (VD `threads_anhlt_alert_bot`).
3. BotFather trả về **token** dạng `123456789:AAF...`. Copy token này.

### A2. Lấy chat_id (nơi nhận cảnh báo)

1. Mở bot vừa tạo, nhắn **một tin bất kỳ** (VD `hello`) — bắt buộc vì bot không thể chủ động nhắn trước.
2. Mở trình duyệt, truy cập URL sau (thay `<TOKEN>` bằng token ở A1):

   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

3. Tìm trong JSON trả về trường `chat` → `id` (dạng số, VD `123456789`). Đó là `TELEGRAM_CHAT_ID`.

   > Nếu muốn nhận cảnh báo ở **group/channel**: thêm bot vào group/channel đó, gửi 1 tin, rồi
   > `getUpdates` sẽ trả `id` dạng số âm của group (VD `-100123456789`) hoặc `channel_post`.
   > Có thể dùng luôn giá trị đó cho `TELEGRAM_CHAT_ID`.

---

## B. Threads (Meta)

Bot dùng **Threads API chính thức** của Meta (miễn phí, giới hạn 2.200 query keyword search/24h).

### B1. Tạo Meta app

1. Vào [developers.facebook.com/apps](https://developers.facebook.com/apps) → **Create app**.
2. Chọn use case **Threads** (nếu trình tạo app hỏi) — app sẽ có **2 App ID/Secret** (Facebook và Threads). Với Threads API, dùng **Threads App ID** và **Threads App Secret** (xem ở *App settings → Basic*).
3. Trong *App settings → Basic*: thêm **Privacy Policy URL** (có thể dùng URL bất kỳ công khai, VD link GitHub Pages) — cần để nộp App Review và chuyển app sang Live.

### B2. Thêm chính bạn làm Threads Tester

App ở chế độ *Development* thì tester được cấp quyền ngay (không cần chờ App Review) — dùng cho giai đoạn chạy thử.

1. App Dashboard → **App roles** → **Roles** → bấm **Add People** → chọn **Threads Tester**.
2. Nhập username Threads của bạn và gửi lời mời.
3. Mở [threads.com/settings/account](https://www.threads.com/settings/account) → mục **Website permissions** → **Accept** lời mời.

### B3. Lấy Threads access token

**Cách nhanh nhất — Graph API Explorer:**

1. Mở [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer).
2. Chọn đúng Meta app vừa tạo.
3. Mục *User or Page* chọn chính tài khoản của bạn, bấm **Generate Access Token** (đăng nhập Instagram/Threads khi được hỏi).
4. Thêm các quyền: `threads_basic`, `threads_read_replies` và `threads_keyword_search`.
   > Nếu `threads_keyword_search` **không xuất hiện** trong danh sách quyền → nghĩa là app chưa có
   > permission này. Vẫn tạo token với 2 quyền còn lại và làm tiếp bước B5 (nộp App Review).
   > Trong lúc chờ duyệt, keyword search chỉ tìm được bài của chính tài khoản của bạn.
5. Token trả về là **short-lived (hết hạn sau ~1 giờ)** → đổi ngay sang long-lived ở B4.

**Cách tự động (Authorization Window):** mở URL dạng:

```
https://threads.com/oauth/authorize?client_id=<THREADS_APP_ID>&redirect_uri=<REDIRECT_URI>&scope=threads_basic,threads_read_replies,threads_keyword_search&response_type=code
```

`redirect_uri` phải khớp chính xác URI đã khai trong *Threads use case settings* của app. Sau khi
đăng nhập, Threads redirect về `redirect_uri?code=...` — lấy `code` và đổi lấy token:

```bash
curl -X POST https://graph.threads.com/oauth/access_token \
  -F client_id=<THREADS_APP_ID> \
  -F client_secret=<THREADS_APP_SECRET> \
  -F grant_type=authorization_code \
  -F redirect_uri=<REDIRECT_URI> \
  -F code=<AUTHORIZATION_CODE>
```

### B4. Đổi sang long-lived token (60 ngày)

```bash
curl -X GET "https://graph.threads.com/oauth/access_token?grant_type=th_exchange_token&client_secret=<THREADS_APP_SECRET>&access_token=<TOKEN_NGAN_HAN>"
```

Lưu `access_token` trả về — dùng cho `.env` (giá trị `THREADS_ACCESS_TOKEN`).

### B5. Nộp App Review cho `threads_keyword_search`

> ⚠️ **Quan trọng:** khi chưa được duyệt, API keyword search **chỉ trả bài của chính tài khoản
> đang cấp token**. Muốn quét toàn Threads thì bắt buộc phải qua bước này (thường mất vài ngày).

1. App Dashboard → **App Review** → **Permissions and Features** → tìm **threads_keyword_search** → **Request**.
2. Mô tả use case trung thực, VD: *"App theo dõi bài viết công khai theo từ khóa để gửi cảnh báo cho chính chủ sở hữu tài khoản (không đăng bài thay mặt người dùng, không hiển thị nội dung người khác)."*
3. Meta có thể yêu cầu video demo — quay màn hình bot đang search từ khóa và hiển thị kết quả.
4. Sau khi duyệt: chuyển app sang **Live** (*App Dashboard → App Mode → Live*) để permission có hiệu lực với mọi user (với chính bạn thì không cần chờ Live).

---

## C. Cấu hình `.env` và chạy bot

1. Copy file mẫu:

   ```bash
   copy .env.example .env
   ```

2. Mở `.env` và điền:

   ```ini
   THREADS_ACCESS_TOKEN=THQVJ...          # token long-lived ở B4
   TELEGRAM_BOT_TOKEN=123456789:AAF...    # token ở A1
   TELEGRAM_CHAT_ID=123456789             # chat id ở A2
   ```

3. Cài đặt và chạy:

   ```bash
   python -m venv .venv
   .venv\Scripts\python -m pip install -e ".[dev]"
   .venv\Scripts\python -m app.main
   ```

   Bot sẽ gửi 1 tin "🤖 Bot theo dõi Threads đã chạy..." về Telegram khi khởi động thành công.

4. Sửa danh sách từ khóa trong `keywords.json` (array JSON) rồi khởi động lại bot.

## D. Test thử pipeline

1. Chạy bot (bước C).
2. Đăng một bài **trên chính tài khoản Threads của bạn** có chứa từ khóa, VD: *"Đang tìm khóa học miễn phí AI, ai có gợi ý?"*.
3. Đợi tới chu kỳ quét tiếp theo (5 phút) — bạn sẽ nhận cảnh báo trên Telegram với nút "Mở trên Threads".
4. Nếu bot đã được App Review duyệt, bài của **bất kỳ ai** trùng từ khóa đều được báo.

## E. Bảo trì token

- **Long-lived token** hết hạn sau **60 ngày**. Refresh trước khi hết hạn:

  ```bash
  curl -X GET "https://graph.threads.com/refresh_access_token?grant_type=th_refresh_token&access_token=<LONG_LIVED_TOKEN>"
  ```

  Token mới trả về lại có hiệu lực 60 ngày → cập nhật vào `.env` và khởi động lại bot.

- Kiểm tra trạng thái token bất kỳ lúc nào bằng [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/).

- Permission grant của user public có hiệu lực 90 ngày; mỗi lần refresh token sẽ gia hạn thêm.

## Lỗi thường gặp

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| Telegram báo "Forbidden: bot was blocked" | Bạn chưa nhắn tin cho bot (bước A2) — nhắn 1 tin rồi chạy lại. |
| API Threads trả `(#10) ... does not have permission` | App chưa được cấp quyền tương ứng — làm lại B5 (App Review) hoặc kiểm tra token tạo đúng quyền ở B3. |
| Search chỉ ra bài của chính mình | Bình thường khi `threads_keyword_search` chưa được duyệt — chờ kết quả App Review. |
| `Unsupported get request` / lỗi 400 | Token sai app hoặc đã hết hạn — kiểm tra bằng Access Token Debugger, refresh ở phần E. |
| Bot chạy nhưng không gửi cảnh báo | Kiểm tra log console: lỗi search từng keyword được in rõ; kiểm tra `keywords.json` và múi giờ. |
