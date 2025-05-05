# راهنمای استقرار پروژه پلاس پی‌تی‌تی

این راهنما مراحل استقرار پروژه پلاس پی‌تی‌تی را در سرور توضیح می‌دهد.

## پیش‌نیازها

برای استقرار این پروژه، سرور شما باید دارای موارد زیر باشد:

1. سیستم عامل لینوکس (ترجیحاً Ubuntu 22.04 یا بالاتر)
2. Docker نسخه 24.0.0 یا بالاتر
3. Docker Compose نسخه 2.20.0 یا بالاتر
4. حداقل 4 گیگابایت رم
5. حداقل 20 گیگابایت فضای ذخیره‌سازی
6. دسترسی به اینترنت برای دانلود ایمیج‌های داکر

## مراحل استقرار

### 1. کلون کردن مخزن

```bash
git clone https://github.com/yourusername/plusptt.git
cd plusptt
```

### 2. ایجاد و تنظیم فایل .env

```bash
# ایجاد فایل .env در پوشه docker
cp docker/.env.example docker/.env
```

فایل docker/.env را با استفاده از یک ویرایشگر متنی باز کنید و موارد زیر را تنظیم کنید:

```
# تنظیمات پایگاه داده
POSTGRES_PASSWORD=your_strong_password

# تنظیمات JWT
JWT_SECRET=your_jwt_secret_at_least_32_chars_long

# تنظیمات دیگر بر اساس نیاز پروژه...
```

### 3. تنظیم نام دامنه

اگر می‌خواهید از یک نام دامنه استفاده کنید، موارد زیر را در فایل .env تنظیم کنید:

```
SITE_URL=https://your-domain.com
API_EXTERNAL_URL=https://your-domain.com
ADDITIONAL_REDIRECT_URLS=https://your-domain.com

# تنظیمات فرانت‌اند
REACT_APP_API_BASE_URL=https://your-domain.com

# تنظیمات بک‌اند
DJANGO_ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
```

### 4. تنظیم SSL (اختیاری)

برای فعال‌سازی SSL، موارد زیر را در فایل .env تنظیم کنید:

```
ENABLE_SSL=true
```

همچنین باید فایل‌های گواهینامه SSL را در مسیر مناسب قرار دهید:

```bash
mkdir -p docker/volumes/nginx/ssl
cp your-certificate.crt docker/volumes/nginx/ssl/certificate.crt
cp your-certificate-key.key docker/volumes/nginx/ssl/certificate.key
```

### 5. راه‌اندازی سرویس‌ها

```bash
cd docker
docker-compose up -d
```

### 6. ایجاد کاربر مدیر (Super Admin)

```bash
docker exec -it plusptt-backend python manage.py createsuperuser
```

### 7. بررسی وضعیت سرویس‌ها

```bash
docker-compose ps
```

## پیکربندی‌های پیشرفته

### تنظیم محدودیت‌های حافظه و CPU

برای مدیریت بهتر منابع، می‌توانید محدودیت‌های حافظه و CPU را در فایل docker-compose.yml تنظیم کنید:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
  
  # سایر سرویس‌ها...
```

### پشتیبان‌گیری از داده‌ها

برای پشتیبان‌گیری منظم از پایگاه داده، می‌توانید از یک اسکریپت bash استفاده کنید:

```bash
#!/bin/bash
# فایل: backup.sh

BACKUP_DIR=/path/to/backup/directory
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# پشتیبان‌گیری از پایگاه داده
docker exec supabase-db pg_dump -U postgres postgres > $BACKUP_DIR/plusptt_db_$DATE.sql

# فشرده‌سازی فایل پشتیبان
gzip $BACKUP_DIR/plusptt_db_$DATE.sql

# حذف فایل‌های پشتیبان قدیمی‌تر از 30 روز
find $BACKUP_DIR -name "plusptt_db_*.sql.gz" -type f -mtime +30 -delete
```

این اسکریپت را در crontab سیستم قرار دهید تا به صورت خودکار اجرا شود.

### مسیریابی دامنه

اگر از یک نام دامنه استفاده می‌کنید، باید رکوردهای DNS مناسب را تنظیم کنید:

1. رکورد A یا CNAME که به آدرس IP سرور شما اشاره می‌کند.
2. اگر از LiveKit با WebRTC استفاده می‌کنید، ممکن است نیاز به تنظیم رکوردهای SRV داشته باشید.

## عیب‌یابی

### بررسی لاگ‌ها

برای بررسی لاگ سرویس‌ها:

```bash
# لاگ همه سرویس‌ها
docker-compose logs

# لاگ یک سرویس خاص
docker-compose logs backend
docker-compose logs nginx
```

### مشکلات رایج

1. **خطای اتصال به پایگاه داده**: 
   - بررسی کنید که سرویس db در حال اجرا باشد.
   - مطمئن شوید که تنظیمات پایگاه داده در فایل .env صحیح باشد.

2. **مشکلات دسترسی به فایل‌های استاتیک**:
   - دستور زیر را اجرا کنید:
   ```bash
   docker exec -it plusptt-backend python manage.py collectstatic --noinput
   ```

3. **مشکلات SSL**:
   - مطمئن شوید که گواهینامه‌ها در مسیر صحیح قرار گرفته‌اند.
   - بررسی کنید که گواهینامه‌ها منقضی نشده باشند.

## به‌روزرسانی

برای به‌روزرسانی پروژه به آخرین نسخه:

```bash
# دریافت آخرین تغییرات
git pull

# بازسازی و راه‌اندازی مجدد سرویس‌ها
cd docker
docker-compose down
docker-compose up -d --build
```

## وضعیت سرویس‌ها پس از راه‌اندازی

پس از راه‌اندازی موفق، سرویس‌های زیر باید در دسترس باشند:

1. **پنل مدیریت**: http://your-domain.com
2. **API بک‌اند**: http://your-domain.com/api/
3. **پنل ادمین جنگو**: http://your-domain.com/admin/
4. **پنل مدیریت سوپابیس**: http://your-domain.com/project/default
5. **LiveKit**: ws://your-domain.com/livekit/ (برای WebSocket)

## اتمام

در صورت نیاز به کمک بیشتر، لطفاً با تیم پشتیبانی تماس بگیرید یا یک issue در مخزن GitHub ایجاد کنید. 