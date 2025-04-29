#!/bin/sh
set -e
python manage.py migrate --noinput
exec gunicorn admin_panel.wsgi:application --bind 0.0.0.0:8010 --workers 3
