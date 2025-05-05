# بک‌اند پلاس پی‌تی‌تی

این پروژه بخش بک‌اند پلاس پی‌تی‌تی است که با استفاده از Django و Django REST Framework ساخته شده است.

## نیازمندی‌ها

برای اجرای این پروژه به موارد زیر نیاز دارید:

```
Python >= 3.9
PostgreSQL >= 15.0 (برای محیط تولید)
```

## نصب وابستگی‌ها

```bash
# ایجاد محیط مجازی
python -m venv venv
source venv/bin/activate  # Linux/macOS
# یا
venv\Scripts\activate  # Windows

# نصب وابستگی‌ها
pip install -r requirements.txt
```

## وابستگی‌های اصلی

در فایل `requirements.txt` نیازمندی‌های زیر تعریف شده‌اند:

```
# فریم‌ورک‌های اصلی
Django==5.2
djangorestframework==3.16.0
django-cors-headers==4.7.0
gunicorn==23.0.0

# پایگاه داده و ابزارهای مرتبط
psycopg2-binary==2.9.10

# سرویس‌های خارجی و API
supabase==2.15.1
livekit==1.0.6
requests==2.31.0

# مدیریت محیط و تنظیمات
python-dotenv==1.1.0

# امنیت
cryptography>=41.0.5
PyJWT>=2.8.0

# ابزارهای کمکی
pytz>=2023.3
Pillow>=10.0.0
six>=1.16.0
```

## راه‌اندازی

برای اجرای برنامه در محیط توسعه:

```bash
# اجرای مهاجرت‌ها
python manage.py migrate

# ایجاد کاربر مدیر
python manage.py createsuperuser

# اجرای سرور توسعه
python manage.py runserver
```

## ساختار پروژه

```
backend/
├── admin_panel/           # برنامه اصلی پروژه (تنظیمات، URL‌ها و ...)
│   ├── settings.py        # تنظیمات پروژه
│   ├── urls.py            # تعریف URL‌های اصلی
│   ├── db_routers.py      # روتر دیتابیس برای اتصال به Supabase
│   └── middleware.py      # میان‌افزارها
├── console/               # برنامه کنسول مدیریت
│   ├── models.py          # تعریف مدل‌های داده
│   ├── views.py           # نمایش‌ها و API‌ها
│   ├── serializers.py     # سریالایزرها برای API
│   ├── urls.py            # URL‌های API
│   └── supabase_client.py # کلاینت اتصال به Supabase
├── static/                # فایل‌های استاتیک
├── manage.py              # فایل مدیریت Django
├── requirements.txt       # وابستگی‌ها
└── Dockerfile             # پیکربندی Docker
```

## API‌های اصلی

```
/api/auth/login/           # ورود کاربران
/api/auth/logout/          # خروج کاربران
/api/channels/             # مدیریت کانال‌ها
/api/channels/{id}/        # جزئیات و ویرایش کانال مشخص
/api/users/                # مدیریت کاربران
/api/users/{id}/           # جزئیات و ویرایش کاربر مشخص
/api/livekit/              # API LiveKit
```

## مدل‌های داده

سه مدل اصلی در سیستم وجود دارد:

1. **Channel**: مدل کانال با شناسه منحصربفرد و لیست کاربران مجاز
2. **User**: مدل کاربر با اطلاعات دسترسی و نقش
3. **SuperAdmin**: مدل مدیر ارشد با اطلاعات مدیریتی

## اجرا با داکر

برای اجرا با استفاده از Docker:

```bash
# ساخت ایمیج
docker build -t plusptt-backend .

# اجرا
docker run -p 8010:8010 plusptt-backend
```

## راهنمای Docker Compose

برای اجرای کل پروژه با استفاده از Docker Compose:

```bash
# در ریشه پروژه اصلی
cd ../
docker-compose -f docker/docker-compose.yml up
``` 