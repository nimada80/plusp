# راهنمای سرویس‌های پروژه پلاس پی‌تی‌تی

این مستند شرح مختصری از سرویس‌های موجود در پروژه پلاس پی‌تی‌تی و نحوه پیکربندی آن‌ها را ارائه می‌دهد.

## معماری کلی

پروژه پلاس پی‌تی‌تی از معماری میکروسرویس استفاده می‌کند و شامل چندین سرویس مستقل است که از طریق شبکه با یکدیگر ارتباط برقرار می‌کنند:

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│   Nginx   │────▶│  Frontend │────▶│  Backend  │
└───────────┘     └───────────┘     └───────────┘
       │                │                  │
       │                │                  │
       ▼                ▼                  ▼
┌───────────┐     ┌───────────┐     ┌───────────┐
│  LiveKit  │◀───▶│  Supabase │◀───▶│ PostgreSQL│
└───────────┘     └───────────┘     └───────────┘
```

## سرویس‌های اصلی

### 1. بک‌اند (Django)

بک‌اند پروژه با استفاده از Django و Django REST Framework پیاده‌سازی شده است.

**فایل‌های کلیدی**:
- `backend/Dockerfile`: تنظیمات ساخت ایمیج داکر
- `backend/requirements.txt`: وابستگی‌های پایتون
- `backend/admin_panel/settings.py`: تنظیمات اصلی جنگو
- `backend/console/views.py`: API‌ها و نمایش‌ها

**پورت‌ها**:
- پورت داخلی: 8010
- پورت بیرونی: 8010 (قابل تنظیم)

**وابستگی‌ها**:
- پایگاه داده PostgreSQL
- سوپابیس (برای احراز هویت)
- لایوکیت (برای ارتباطات زنده)

**نحوه راه‌اندازی**:
```bash
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn admin_panel.wsgi:application --bind 0.0.0.0:8010 --workers 3
```

### 2. فرانت‌اند (React)

فرانت‌اند با استفاده از React و Material UI پیاده‌سازی شده است.

**فایل‌های کلیدی**:
- `frontend/Dockerfile`: تنظیمات ساخت ایمیج داکر
- `frontend/package.json`: وابستگی‌های JavaScript
- `frontend/src/App.js`: کامپوننت اصلی
- `frontend/nginx.conf`: تنظیمات سرور Nginx برای سرو فایل‌های استاتیک

**پورت‌ها**:
- پورت داخلی: 80 (nginx)
- پورت بیرونی: 3010 (قابل تنظیم)

**وابستگی‌ها**:
- بک‌اند Django برای API‌ها
- سوپابیس (برای احراز هویت)
- لایوکیت (برای ارتباطات زنده)

**نحوه راه‌اندازی**:
```bash
cd frontend
npm install
npm run build
# سپس سرو با استفاده از Nginx
```

### 3. سوپابیس (Supabase)

سوپابیس برای مدیریت احراز هویت، ذخیره‌سازی و دسترسی به پایگاه داده استفاده می‌شود.

**اجزای سوپابیس**:
- `studio`: پنل مدیریت سوپابیس
- `kong`: مدیریت API
- `auth`: احراز هویت
- `rest`: RESTful API برای پایگاه داده
- `realtime`: قابلیت‌های realtime

**پورت‌ها**:
- پورت Kong: 8000 (داخلی)

**تنظیمات کلیدی**:
- کلیدهای JWT: `JWT_SECRET`, `ANON_KEY`, و `SERVICE_ROLE_KEY`
- تنظیمات احراز هویت: `DISABLE_SIGNUP`, `ENABLE_EMAIL_SIGNUP`, و غیره

### 4. لایوکیت (LiveKit)

لایوکیت برای پشتیبانی از ارتباطات زنده صوتی و تصویری استفاده می‌شود.

**فایل‌های کلیدی**:
- `livekit/config.yaml`: تنظیمات سرور LiveKit
- `livekit/env.example`: نمونه تنظیمات محیطی

**پورت‌ها**:
- پورت اصلی: 7880
- پورت‌های RTC: 7881-7888
- پورت TURN: 3478

**وابستگی‌ها**:
- Redis (برای ذخیره‌سازی وضعیت)

**تنظیمات کلیدی**:
- کلیدهای API: `LIVEKIT_API_KEY` و `LIVEKIT_API_SECRET`
- تنظیمات اتاق‌ها: `LIVEKIT_ROOM_MAX_PARTICIPANTS` و `LIVEKIT_ROOM_EMPTY_TIMEOUT`

### 5. انجین‌ایکس (Nginx)

Nginx به عنوان وب سرور و پروکسی معکوس برای هدایت درخواست‌ها بین سرویس‌های مختلف استفاده می‌شود.

**فایل‌های کلیدی**:
- `nginx/nginx.conf`: تنظیمات اصلی Nginx

**پورت‌ها**:
- پورت HTTP: 80
- پورت HTTPS: 443 (اگر SSL فعال باشد)

**مسیرهای اصلی**:
- `/`: فرانت‌اند React
- `/api/`: بک‌اند Django
- `/project/`: پنل مدیریت سوپابیس
- `/livekit/`: سرور LiveKit

## پیکربندی سیستم

### تنظیمات محیطی

تمام تنظیمات محیطی باید در فایل `docker/.env` قرار داده شوند. این فایل شامل تنظیمات کلیدی برای همه سرویس‌هاست.

### مدیریت منابع

برای مدیریت منابع، می‌توانید محدودیت‌های CPU و حافظه را در فایل `docker-compose.yml` تنظیم کنید:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### پشتیبان‌گیری

پشتیبان‌گیری از پایگاه داده PostgreSQL (که شامل داده‌های سوپابیس نیز می‌شود) باید به صورت منظم انجام شود:

```bash
docker exec supabase-db pg_dump -U postgres postgres > backup.sql
```

## مسیریابی و CORS

تنظیمات CORS برای ارتباط بین سرویس‌ها در چند جا انجام می‌شود:

1. **Nginx**: در فایل `nginx/nginx.conf` با استفاده از هدرهای `Access-Control-Allow-Origin`
2. **بک‌اند Django**: در فایل `settings.py` با استفاده از `CORS_ALLOWED_ORIGINS`
3. **سوپابیس**: تنظیمات Kong در فایل `docker/volumes/api/kong.yml`

## مدیریت SSL

برای فعال‌سازی SSL:

1. فایل‌های گواهینامه SSL را در مسیر `docker/volumes/nginx/ssl/` قرار دهید
2. تنظیم `ENABLE_SSL=true` در فایل `.env`
3. مطمئن شوید که `SITE_URL` و `API_EXTERNAL_URL` با `https://` شروع می‌شوند

## اشکال‌زدایی عمومی

### نحوه بررسی لاگ‌ها

```bash
# لاگ سرویس بک‌اند
docker logs plusptt-backend

# لاگ سرویس فرانت‌اند
docker logs supabase-nginx

# لاگ سوپابیس
docker logs supabase-auth
docker logs supabase-db

# لاگ لایوکیت
docker logs livekit
```

### مشکلات رایج

1. **خطاهای دسترسی CORS**: بررسی تنظیمات CORS در Nginx و بک‌اند
2. **خطاهای اتصال به بانک اطلاعاتی**: بررسی وضعیت سرویس PostgreSQL
3. **مشکلات احراز هویت**: بررسی تنظیمات و لاگ‌های سوپابیس
4. **مشکلات ارتباطات زنده**: بررسی تنظیمات و لاگ‌های لایوکیت

## مدیریت سرویس‌ها

```bash
# راه‌اندازی همه سرویس‌ها
docker-compose up -d

# توقف همه سرویس‌ها
docker-compose down

# راه‌اندازی مجدد یک سرویس خاص
docker-compose restart backend

# بازسازی و راه‌اندازی مجدد
docker-compose up -d --build
``` 