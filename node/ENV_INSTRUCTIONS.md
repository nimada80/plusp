# راهنمای تنظیم متغیرهای محیطی

برای اینکه سرویس احراز هویت به درستی کار کند، باید متغیرهای محیطی زیر را در فایل `.env` در پوشه `docker` اضافه کنید:

```
# Supabase connection
SUPABASE_URL=http://kong:8000
SUPABASE_SERVICE_ROLE_KEY=${SERVICE_ROLE_KEY}

# LiveKit configuration
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret
LIVEKIT_HOST=livekit:7880

# Auth service settings
AUTH_SERVICE_PORT=3030
AUTH_SERVICE_HOST=0.0.0.0
```

## نکات مهم

1. مقدار `SERVICE_ROLE_KEY` همان کلید سرویس Supabase است که در فایل `.env` قبلاً تنظیم شده است.

2. مقادیر `LIVEKIT_API_KEY` و `LIVEKIT_API_SECRET` باید همان مقادیری باشند که در فایل `livekit/config.yaml` تنظیم شده‌اند.

3. مقدار `LIVEKIT_HOST` به صورت `livekit:7880` تنظیم شده تا بتواند در شبکه داخلی Docker به سرویس LiveKit متصل شود.

## آزمایش سرویس

پس از تنظیم متغیرهای محیطی و راه‌اندازی سرویس با Docker Compose، می‌توانید با ارسال یک درخواست POST به آدرس زیر، عملکرد سرویس را آزمایش کنید:

```bash
curl -X POST http://localhost:3030/authenticate \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "userpassword"}'
```

همچنین می‌توانید وضعیت سلامت سرویس را با درخواست زیر بررسی کنید:

```bash
curl http://localhost:3030/health
``` 