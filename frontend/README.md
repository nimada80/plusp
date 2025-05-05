# پنل مدیریت پلاس پی‌تی‌تی

این پروژه بخش فرانت‌اند پنل مدیریت پلاس پی‌تی‌تی است که با استفاده از React و Material UI ساخته شده است.

## نیازمندی‌ها

برای اجرای این پروژه به موارد زیر نیاز دارید:

```
Node.js >= 18.x
npm >= 9.x
```

## وابستگی‌های اصلی

```
# کتابخانه‌های اصلی
react: 18.2.0
react-dom: 18.2.0
react-router-dom: 6.22.1
react-scripts: 5.0.1

# رابط کاربری
@mui/material: 7.0.2
@mui/icons-material: 7.0.2
@emotion/react: 11.14.0
@emotion/styled: 11.14.0
@emotion/cache: 11.14.0
stylis: 4.3.6
stylis-plugin-rtl: 2.1.1

# ارتباط با API
axios: 1.8.4
@supabase/supabase-js: 2.49.4

# تست
@testing-library/react: 16.3.0
@testing-library/jest-dom: 6.6.3
@testing-library/user-event: 13.5.0
```

## نصب و راه‌اندازی

برای نصب وابستگی‌ها و اجرای پروژه در محیط توسعه:

```bash
# نصب وابستگی‌ها
npm install

# اجرای برنامه در محیط توسعه
npm start
```

برای ساخت نسخه تولیدی:

```bash
npm run build
```

## ساختار پروژه

```
frontend/
├── src/                    # کدهای اصلی پروژه
│   ├── components/         # کامپوننت‌های React
│   │   ├── ChannelManagement.js  # مدیریت کانال‌ها
│   │   ├── UserManagement.js     # مدیریت کاربران
│   │   ├── Login.js              # صفحه ورود
│   │   └── Sidebar.js            # نوار کناری
│   ├── utils/              # ابزارهای کمکی
│   │   └── api.js          # توابع ارتباط با API
│   ├── App.js              # کامپوننت اصلی
│   ├── theme.js            # تنظیمات تم Material UI
│   ├── index.js            # نقطه ورود برنامه
│   └── RequireAuth.js      # محافظت از مسیرها
├── public/                 # فایل‌های استاتیک
├── Dockerfile              # پیکربندی Docker
└── package.json            # تنظیمات پروژه و وابستگی‌ها
```

## ویژگی‌ها

- مدیریت کانال‌ها (افزودن، ویرایش، حذف)
- مدیریت کاربران (افزودن، ویرایش، حذف، تغییر وضعیت)
- تخصیص کاربران به کانال‌ها
- رابط کاربری راست به چپ (RTL) برای زبان فارسی
- احراز هویت و کنترل دسترسی
- ارتباط با API بک‌اند
- پشتیبانی از Supabase

## اجرا با داکر

برای اجرا با استفاده از Docker:

```bash
# ساخت ایمیج
docker build -t plusptt-frontend .

# اجرا
docker run -p 3010:80 plusptt-frontend
```

## راهنمای Docker Compose

برای اجرای کل پروژه با استفاده از Docker Compose:

```bash
# در ریشه پروژه اصلی
cd ../
docker-compose -f docker/docker-compose.yml up
```
