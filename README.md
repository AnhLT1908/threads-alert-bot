# Threads Alert Bot

Bot theo dõi từ khóa trên **Threads**, khi có bài viết trùng từ khóa sẽ gửi cảnh báo về **Telegram**.

## Trạng thái

- [x] HLD (xem `docs/HLD.md`)
- [x] W1: Scaffold dự án
- [ ] W2-W8: đang implement

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env   # điền THREADS_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

## Chạy

```bash
.venv\Scripts\python -m app.main
```

Hướng dẫn chi tiết tạo Meta app + Telegram bot: xem `docs/SETUP.md` (sẽ có ở W8).
