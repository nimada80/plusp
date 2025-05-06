#!/usr/bin/env python
"""
اسکریپت تست برای بررسی عملکرد حذف کاربر
"""

import logging
import json
import os
import sys
import uuid

# تنظیم مسیر برای پیدا کردن ماژول‌های پروژه
sys.path.insert(0, '/app')

# تنظیم متغیر محیطی DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

try:
    # راه‌اندازی جنگو
    import django
    django.setup()
    
    # وارد کردن ماژول‌های لازم
    from console.views import UserViewSet, _make_request
    from rest_framework.test import APIRequestFactory, force_authenticate
    from rest_framework.response import Response
    from django.contrib.auth.models import User
    
    # ایجاد یک کاربر مدیر برای احراز هویت
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        logger.info("ایجاد کاربر مدیر برای احراز هویت")
        admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin_test@example.com',
            password='Admin123!'
        )
    
    # تنظیم متغیرهای تست
    test_user_id = str(uuid.uuid4())  # ایجاد یک UUID معتبر
    logger.info(f"شناسه کاربر تست: {test_user_id}")
    
    # بررسی آیا کاربر وجود دارد
    logger.info(f"بررسی وجود کاربر با شناسه {test_user_id}")
    user_data = _make_request('GET', f"/rest/v1/users?uid=eq.{test_user_id}")
    if not user_data or (isinstance(user_data, list) and len(user_data) == 0):
        logger.warning(f"کاربر با شناسه {test_user_id} وجود ندارد")
        # اگر کاربر وجود ندارد، یک کاربر تست ایجاد کنیم
        from console.supabase_client import create_user
        logger.info("ایجاد کاربر تست جدید")
        new_user = create_user(
            username="testuser",
            password="Test123!",
            role="regular",
            active=True
        )
        if new_user:
            if isinstance(new_user, dict) and 'uid' in new_user:
                test_user_id = new_user.get('uid')
            elif isinstance(new_user, dict) and 'id' in new_user:
                test_user_id = new_user.get('id')
            logger.info(f"کاربر تست با شناسه {test_user_id} ایجاد شد")
        else:
            logger.error("خطا در ایجاد کاربر تست")
    else:
        logger.info(f"کاربر با شناسه {test_user_id} یافت شد")
    
    # اجرای متد destroy برای حذف کاربر با احراز هویت
    factory = APIRequestFactory()
    request = factory.delete(f'/users/{test_user_id}/')
    
    # احراز هویت درخواست با کاربر مدیر
    logger.info(f"احراز هویت درخواست با کاربر مدیر {admin_user.username}")
    force_authenticate(request, user=admin_user)
    
    user_viewset = UserViewSet.as_view({'delete': 'destroy'})
    
    logger.info(f"ارسال درخواست حذف کاربر با شناسه {test_user_id}")
    response = user_viewset(request, pk=test_user_id)
    
    if isinstance(response, Response):
        logger.info(f"کد وضعیت: {response.status_code}")
        try:
            logger.info(f"داده‌های پاسخ: {json.dumps(response.data, ensure_ascii=False)}")
        except:
            logger.info(f"داده‌های پاسخ: {response.data}")
    else:
        logger.info(f"نوع پاسخ: {type(response)}")
        logger.info(f"پاسخ: {response}")
    
    # بررسی آیا کاربر با موفقیت حذف شده است
    logger.info(f"بررسی حذف کاربر با شناسه {test_user_id}")
    user_check = _make_request('GET', f"/rest/v1/users?uid=eq.{test_user_id}")
    if user_check is None or (isinstance(user_check, list) and len(user_check) == 0):
        logger.info(f"کاربر با شناسه {test_user_id} با موفقیت از جدول users حذف شده است")
    else:
        logger.warning(f"کاربر با شناسه {test_user_id} هنوز در جدول users وجود دارد")
    
    # بررسی آیا کاربر از auth حذف شده است
    auth_check = _make_request('GET', f"/auth/v1/admin/users/{test_user_id}")
    if auth_check is None or (isinstance(auth_check, list) and len(auth_check) == 0):
        logger.info(f"کاربر با شناسه {test_user_id} با موفقیت از auth حذف شده است")
    else:
        logger.warning(f"کاربر با شناسه {test_user_id} هنوز در auth وجود دارد")
        
except Exception as e:
    logger.error(f"خطا در اجرای تست: {str(e)}")
    import traceback
    logger.error(traceback.format_exc()) 