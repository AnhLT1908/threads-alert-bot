# Threads Alert Bot

Bot theo dõi từ khóa trên **Threads**, khi có bài viết trùng từ khóa sẽ gửi cảnh báo về **Telegram**.

## Tính năng

- Quét Threads theo danh sách từ khóa (`keywords.json`) qua **Threads API chính thức** (miễn phí).
- Tự động tính chu kỳ quét không vượt rate limit 2.200 query/24h (mặc định 5 phút với ≤ 6 từ khóa).
- Match thông minh: không phân biệt hoa thường, tự bỏ dấu tiếng Việt, match nguyên từ
  (tránh "freedom" trùng "free").
- Dedupe qua SQLite — mỗi bài chỉ báo 1 lần, không mất bài khi khởi động lại.
- Cảnh báo Telegram kèm link mở bài + trích nội dung, tự retry và gửi bù khi mạng lỗi.

## Cài đặt nhanh

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env   # điền THREADS_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
.venv\Scripts\python -m app.main
```

## Hướng dẫn đầy đủ

- **Thiết lập Telegram + Meta/Threads app + token**: xem [`docs/SETUP.md`](docs/SETUP.md)
- **Thiết kế hệ thống (HLD)**: xem [`docs/HLD.md`](docs/HLD.md)

## Cấu trúc

```
app/
├── main.py              # entrypoint + vòng lặp quét
├── config.py            # cấu hình từ .env
├── keywords.py          # nạp danh sách từ khóa
├── scheduler.py         # tính chu kỳ quét theo rate limit
├── threads_client.py    # gọi Threads Graph API (keyword_search)
├── matcher.py           # so khớp từ khóa
├── storage.py           # SQLite: dedupe + state + tin lỗi
└── notifier.py          # gửi cảnh báo Telegram
```

## Chạy test

```bash
.venv\Scripts\python -m pytest --cov=app
```
