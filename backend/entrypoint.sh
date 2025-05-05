#!/bin/bash
set -e

# اضافه کردن نصب پکیج های مورد نیاز
pip install livekit-api==1.0.2

# اجرای مهاجرت‌های دیتابیس
python manage.py migrate --noinput

# اجرای سرور Django
exec gunicorn admin_panel.wsgi:application --bind 0.0.0.0:8010 --workers 3
