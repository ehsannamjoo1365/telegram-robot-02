# Telegram Automation & Notifications Bot

ربات مستقل اعلان‌رسانی با مقصدهای ثبت‌شده و کنترل مالک.

## فرمان‌ها
- `/start` و `/help`: راهنما
- `/register_here`: ثبت گروه جاری (مالک، داخل گروه)
- `/addchat CHAT_ID`: افزودن مقصد
- `/removechat CHAT_ID`: حذف مقصد
- `/destinations`: فهرست مقصدها
- `/notify متن`: ارسال اعلان به مقصدهای ثبت‌شده (مالک، گفت‌وگوی خصوصی)
- `/id`: شناسه گفتگو

ارسال اعلان فقط به مقصدهایی انجام می‌شود که مالک صریحاً ثبت کرده و فقط با اجرای فرمان /notify. ارسال ناخواسته به کاربران ناشناس پشتیبانی نمی‌شود.

## تنظیمات مستقل
- `BOT_TOKEN`: توکن اختصاصی همین ربات
- `OWNER_ID`: شناسه عددی تلگرام مالک
- `BOT_USERNAME`: (اختیاری) نام کاربری بدون @ برای کنترل تطابق توکن
- `BOT_STATE_FILE`: مسیر فایل مقصدها؛ پیش‌فرض `data/state.json`

## اجرا
```bash
export BOT_TOKEN='توکن اختصاصی'
export OWNER_ID='شناسه عددی مالک'
python bot.py
```
با Docker:
```bash
docker build -t telegram-automation .
docker run -d --restart unless-stopped -e BOT_TOKEN -e OWNER_ID -e BOT_USERNAME -v telegram-automation-data:/app/data telegram-automation
```

فایل مقصدها در volume ذخیره می‌شود؛ بدون volume ممکن است با حذف کانتینر از بین برود. برنامه long polling است و به VPS یا سرویس کانتینری دائمی نیاز دارد.
