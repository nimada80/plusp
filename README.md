# پروژه پلاس پی‌تی‌تی

سیستم مدیریت کانال‌ها با قابلیت ارتباطات زنده صوتی و تصویری و مدیریت کاربران

## معرفی

پلاس پی‌تی‌تی یک سیستم مدیریت ارتباطات است که امکان ایجاد و مدیریت کانال‌ها، کاربران و دسترسی‌ها را فراهم می‌کند. این سیستم شامل یک پنل مدیریت کامل، API برای ارتباط با سرویس‌های مختلف و پشتیبانی از ارتباطات زنده صوتی و تصویری است.

## ویژگی‌ها

- مدیریت کانال‌ها (ایجاد، ویرایش، حذف)
- مدیریت کاربران (ایجاد، ویرایش، حذف، تعیین وضعیت)
- تخصیص کاربران به کانال‌ها
- ارتباطات زنده با استفاده از LiveKit
- رابط کاربری فارسی با پشتیبانی از RTL
- احراز هویت با Supabase
- API‌های RESTful برای تعامل با سیستم
- مقیاس‌پذیری با معماری میکروسرویس و Docker

## معماری

این پروژه از معماری میکروسرویس با اجزای زیر تشکیل شده است:

1. **بک‌اند Django**: ارائه API و مدیریت داده‌ها
2. **فرانت‌اند React**: رابط کاربری پنل مدیریت
3. **LiveKit**: سرویس ارتباطات زنده صوتی و تصویری
4. **Supabase**: مدیریت احراز هویت و ذخیره‌سازی
5. **Nginx**: وب سرور و پروکسی معکوس
6. **Docker**: کانتینرسازی تمام اجزا

## ساختار پروژه

```
./
├── backend/               # بک‌اند Django
│   ├── admin_panel/       # برنامه اصلی (تنظیمات، URL‌ها)
│   ├── console/           # برنامه مدیریت کانال‌ها و کاربران
│   └── requirements.txt   # وابستگی‌های بک‌اند
├── frontend/              # فرانت‌اند React
│   ├── src/               # کدهای اصلی فرانت‌اند
│   └── package.json       # وابستگی‌های فرانت‌اند
├── docker/                # تنظیمات و فایل‌های Docker
│   └── docker-compose.yml # پیکربندی Docker Compose
├── livekit/               # تنظیمات LiveKit
│   └── config.yaml        # پیکربندی سرور LiveKit
├── nginx/                 # تنظیمات Nginx
│   └── nginx.conf         # پیکربندی وب سرور
└── supabase/              # تنظیمات و اسکریپت‌های Supabase
```

## نیازمندی‌ها

### بک‌اند

- Python 3.9+
- Django 5.2
- Django REST Framework 3.16.0
- و سایر وابستگی‌ها در `backend/requirements.txt`

### فرانت‌اند

- Node.js 18+
- React 18.2.0
- Material UI 7.0.2
- و سایر وابستگی‌ها در `frontend/package.json`

### زیرساخت

- Docker و Docker Compose
- PostgreSQL 15+
- Redis (برای LiveKit)
- Nginx

## راه‌اندازی با Docker

ساده‌ترین روش برای راه‌اندازی کل پروژه استفاده از Docker Compose است:

```bash
# کلون کردن مخزن
git clone https://github.com/yourusername/plusptt.git
cd plusptt

# ایجاد فایل .env از نمونه
cp docker/.env.example docker/.env

# ویرایش فایل .env و تنظیم مقادیر مورد نیاز

# راه‌اندازی سرویس‌ها
docker-compose -f docker/docker-compose.yml up -d
```

پس از راه‌اندازی، سرویس‌ها در آدرس‌های زیر در دسترس خواهند بود:

- پنل مدیریت: http://localhost
- API بک‌اند: http://localhost/api/
- پنل ادمین: http://localhost/admin/
- سوپابیس استودیو: http://localhost/project/default

## راه‌اندازی در محیط توسعه

برای توسعه اجزای پروژه به صورت جداگانه می‌توانید از دستورالعمل‌های زیر استفاده کنید:

### بک‌اند

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### فرانت‌اند

```bash
cd frontend
npm install
npm start
```

برای اطلاعات بیشتر به README هر بخش مراجعه کنید.

## مستندات بیشتر

- [مستندات بک‌اند](backend/README.md)
- [مستندات فرانت‌اند](frontend/README.md)
- [مستندات LiveKit](livekit/README.md)

## مجوز

این پروژه تحت مجوز [MIT](LICENSE) منتشر شده است. 