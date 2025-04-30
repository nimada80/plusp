"""
تنظیمات محلی برای محیط داکر
تنظیمات اختصاصی برای اتصال به دیتابیس PostgreSQL از طریق Kong
"""

import os
from pathlib import Path

# مسیر اصلی پروژه - مشابه تعریف در settings.py
BASE_DIR = Path(__file__).resolve().parent.parent

# تنظیمات پایگاه داده با استفاده از Kong
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'supabase': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'supabase_admin',
        'PASSWORD': 'Jhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKI',
        'HOST': 'db',  # دسترسی مستقیم به دیتابیس بدون Kong
        'PORT': '5432',  # پورت پیش‌فرض PostgreSQL
    }
}

# استفاده از روتر دیتابیس برای ارسال همه کوئری‌ها به دیتابیس supabase
DATABASE_ROUTERS = ['admin_panel.db_routers.SupabaseRouter']
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField" 