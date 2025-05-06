#!/bin/bash
set -e

# نصب livekit حذف شد

# اجرای مهاجرت‌های دیتابیس
python manage.py migrate --noinput

# اجرای سرور Django
exec gunicorn admin_panel.wsgi:application --bind 0.0.0.0:8010 --workers 3
