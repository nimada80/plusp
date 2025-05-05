"""
admin_panel/settings.py
Project settings for Django admin_panel:
- CORS configuration to allow requests from React dev server
- CSRF and session cookie settings for cross-site auth in development
- REST framework default auth/permission classes enforcing session auth
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-$uy+k_gm)^s8ih5lfaangra6u+10g^9%3r5)s8evk(5vjyei%*')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CORS configuration - غیر فعال شده چون توسط nginx مدیریت می‌شود
# CORS_ALLOWED_ORIGINS = []
# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOW_CREDENTIALS = False
# CORS_ALLOWED_ORIGIN_REGEXES = []
# CORS_URLS_REGEX = r'^/(api|backend)/.*$'
# CORS_EXPOSE_HEADERS = []
# CORS_ALLOW_HEADERS = []
# CORS_ALLOW_METHODS = []

# Configure CSRF and session cookies to work with cross-site React app
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://localhost:3010', 'http://localhost']

# تنظیمات سشن و CSRF برای محیط توسعه
SESSION_COOKIE_SAMESITE = 'Lax'  # بازگشت به Lax برای محیط توسعه
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_NAME = 'sessionid'
SESSION_SAVE_EVERY_REQUEST = True  # ذخیره سشن در هر درخواست
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 1209600  # دو هفته

CSRF_COOKIE_SAMESITE = 'Lax'  # بازگشت به Lax برای محیط توسعه
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False  # امکان دسترسی از جاوااسکریپت
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_DOMAIN = None
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# امکان درخواست به ادمین بدون CSRF
CSRF_EXEMPT_PATHS = ['/admin/login/', '/api/auth/login/']

# بهبود پیکربندی لاگینگ
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'admin_panel': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# تنظیمات احراز هویت
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# مسیر لاگین
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    # "corsheaders",  # حذف شده چون CORS توسط nginx مدیریت می‌شود
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'rest_framework',
    'console',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # "corsheaders.middleware.CorsMiddleware",  # حذف شده چون CORS توسط nginx مدیریت می‌شود
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "admin_panel.middleware.CustomCsrfMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "admin_panel.middleware.SessionDebugMiddleware",
]

ROOT_URLCONF = "admin_panel.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "admin_panel.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'supabase': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'postgres'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

DATABASE_ROUTERS = ['admin_panel.db_routers.SupabaseRouter']


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = '/app/static/'

# تغییر تنظیمات برای عملکرد درست با nginx
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# آیا از FORCE_SCRIPT_NAME استفاده می‌کنیم یا نه
# جنگو از هدر X-Script-Name استفاده می‌کند اگر تنظیم شده باشد
FORCE_SCRIPT_NAME = None

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST framework settings
REST_FRAMEWORK = {
    # Use Django session authentication for API endpoints by default
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Require authenticated sessions on all API views unless overridden
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# وارد کردن تنظیمات محلی
try:
    from .local_settings import *
except ImportError:
    pass
