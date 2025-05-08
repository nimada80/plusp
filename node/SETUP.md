# راهنمای راه‌اندازی و استفاده از سرویس احراز هویت

## مقدمه

سرویس احراز هویت پلاس پی‌تی‌تی یک سرویس Node.js مبتنی بر Fastify است که وظیفه احراز هویت کاربران و صدور توکن‌های LiveKit برای کانال‌های مجاز را بر عهده دارد. این سرویس با استفاده از Supabase برای احراز هویت و LiveKit برای ارتباطات زنده کار می‌کند.

## پیش‌نیازها

- Docker و Docker Compose
- دسترسی به سرویس‌های Supabase و LiveKit
- تنظیمات محیطی مناسب در فایل `.env` در پوشه `docker`

## گام‌های راه‌اندازی

### 1. اضافه کردن متغیرهای محیطی

متغیرهای محیطی زیر را به فایل `.env` در پوشه `docker` اضافه کنید:

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

### 2. راه‌اندازی با Docker Compose

برای راه‌اندازی کل پروژه، دستور زیر را در پوشه اصلی پروژه اجرا کنید:

```bash
cd docker
docker-compose up -d
```

این دستور تمام سرویس‌های مورد نیاز از جمله سرویس احراز هویت را راه‌اندازی می‌کند.

### 3. بررسی وضعیت سرویس

برای اطمینان از اینکه سرویس به درستی راه‌اندازی شده است، دستور زیر را اجرا کنید:

```bash
curl http://localhost:3030/health
```

در صورت راه‌اندازی موفق، باید پاسخی مشابه زیر دریافت کنید:

```json
{"status":"up","version":"1.0.0"}
```

## نحوه استفاده از سرویس

### احراز هویت و دریافت توکن‌های LiveKit

برای احراز هویت کاربر و دریافت توکن‌های LiveKit، یک درخواست POST به آدرس زیر ارسال کنید:

```
POST http://localhost:3030/authenticate
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "userpassword"
}
```

در صورت موفقیت، پاسخی مشابه زیر دریافت خواهید کرد:

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

### استفاده از توکن‌ها برای اتصال به LiveKit

با استفاده از توکن‌های دریافتی، می‌توانید به کانال‌های LiveKit متصل شوید. برای مثال با استفاده از کتابخانه LiveKit Client:

```javascript
import { Room } from 'livekit-client';

async function connectToChannel(channelData) {
  const room = new Room();
  await room.connect(`ws://${channelData.livekitHost}`, channelData.token);
  console.log(`اتصال به کانال ${channelData.channelName} برقرار شد`);
  return room;
}
```

## عیب‌یابی

### مشکل در اتصال به Supabase

اگر با خطای اتصال به Supabase مواجه شدید، موارد زیر را بررسی کنید:

1. مقادیر `SUPABASE_URL` و `SUPABASE_SERVICE_ROLE_KEY` درست تنظیم شده باشند.
2. سرویس Supabase در حال اجرا باشد.
3. شبکه Docker به درستی پیکربندی شده باشد.

### مشکل در تولید توکن LiveKit

اگر با خطای تولید توکن LiveKit مواجه شدید، موارد زیر را بررسی کنید:

1. مقادیر `LIVEKIT_API_KEY` و `LIVEKIT_API_SECRET` درست تنظیم شده باشند.
2. سرویس LiveKit در حال اجرا باشد.
3. فرمت توکن و دسترسی‌های آن صحیح باشد.

## منابع بیشتر

- [مستندات LiveKit](https://docs.livekit.io)
- [مستندات Supabase](https://supabase.com/docs)
- [مستندات Fastify](https://www.fastify.io/docs/latest) 