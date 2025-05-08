# سرویس احراز هویت پلاس پی‌تی‌تی

این سرویس وظیفه احراز هویت کاربران با استفاده از Supabase و صدور توکن LiveKit برای کانال‌های مجاز را بر عهده دارد.

## عملکرد

1. کاربر ایمیل و رمز عبور خود را به سرویس ارسال می‌کند
2. سرویس با استفاده از Supabase کاربر را احراز هویت می‌کند
3. پس از احراز هویت، لیست کانال‌های مجاز کاربر از جدول `users` استخراج می‌شود
4. نام کانال‌های مجاز با استفاده از جدول `channels` دریافت می‌شود
5. برای هر کانال، یک توکن LiveKit تولید می‌شود
6. توکن‌ها همراه با نام کانال‌ها به کاربر بازگردانده می‌شوند

## API

### `POST /authenticate`

احراز هویت کاربر و دریافت توکن‌های LiveKit برای کانال‌های مجاز

#### درخواست

```json
{
  "email": "user@example.com",
  "password": "userpassword"
}
```

#### پاسخ موفق

```json
{
  "message": "احراز هویت موفق",
  "username": "user",
  "userId": "user-uuid",
  "channels": [
    {
      "token": "livekit-token-for-channel-1",
      "channelUid": "channel-1-uid",
      "channelName": "کانال شماره ۱",
      "livekitHost": "livekit:7880"
    },
    {
      "token": "livekit-token-for-channel-2",
      "channelUid": "channel-2-uid",
      "channelName": "کانال شماره ۲",
      "livekitHost": "livekit:7880"
    }
  ]
}
```

### `GET /health`

بررسی وضعیت سلامت سرویس

#### پاسخ

```json
{
  "status": "up",
  "version": "1.0.0"
}
```

## متغیرهای محیطی مورد نیاز

این سرویس از متغیرهای محیطی زیر استفاده می‌کند که باید در فایل `.env` در پوشه `docker` تنظیم شوند:

```
# متغیرهای Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# متغیرهای LiveKit
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret
LIVEKIT_HOST=livekit:7880

# تنظیمات سرویس
AUTH_SERVICE_PORT=3030
AUTH_SERVICE_HOST=0.0.0.0
```

## راه‌اندازی با Docker

```bash
cd note
docker build -t plusptt-auth-service .
docker run -p 3030:3030 --env-file ../docker/.env plusptt-auth-service
``` 