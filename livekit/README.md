# LiveKit Server

این پوشه شامل تنظیمات داکر برای راه‌اندازی سرور LiveKit برای پشتیبانی از ویدیو کنفرانس و صوت در سیستم است.

## راه‌اندازی

1. ابتدا فایل `.env` را برای تنظیم کلیدها ایجاد کنید:

```bash
cp .env.example .env
```

2. کلیدهای امنیتی را در فایل `.env` ویرایش کنید یا از کلیدهای پیش‌فرض استفاده کنید.

3. برای راه‌اندازی سرور LiveKit از دستور زیر استفاده کنید:

```bash
docker-compose -f docker-compose.livekit.yml up -d
```

یا برای اضافه کردن به کانتینرهای اصلی پروژه:

```bash
docker-compose -f ../docker/docker-compose.yml -f docker-compose.livekit.yml up -d
```

## پورت‌های مورد استفاده

- **7880**: پورت اصلی API و WebSocket
- **7881**: پورت RTMP
- **7882**: پورت UDP و TCP برای WebRTC
- **6380**: پورت Redis (مپ شده به 6379 داخل کانتینر)

## تنظیمات پیکربندی

تنظیمات اصلی سرور LiveKit در فایل `config.yaml` قرار دارد که شامل موارد زیر است:

- تنظیمات شبکه و پورت‌ها
- تنظیمات کیفیت صدا و تصویر
- تنظیمات Redis
- تنظیمات امنیتی و دسترسی

## استفاده در برنامه

برای استفاده از LiveKit در برنامه فرانت‌اند، می‌توانید از کتابخانه‌های رسمی LiveKit استفاده کنید:

- React: `@livekit/components-react`
- JavaScript: `livekit-client`

مثال اتصال به سرور:

```javascript
import { Room } from 'livekit-client';

const room = new Room({
  adaptiveStream: true,
  dynacast: true,
});

await room.connect('http://localhost:7880', token);
```

## ساخت توکن دسترسی

برای تولید توکن JWT برای دسترسی به LiveKit، می‌توانید از سرور بک‌اند خود استفاده کنید. نمونه کد Python:

```python
from livekit import api

api_key = "your_api_key"
api_secret = "your_api_secret"
token = api.AccessToken(api_key, api_secret)
token.add_grant(room_name="room-name", room_join=True, can_publish=True, can_subscribe=True)
jwt = token.to_jwt()
``` 