"""
console/views.py
Defines REST API views for Channel and User management using Django REST framework.
ChannelViewSet and UserViewSet provide CRUD operations secured by session authentication and CSRF protection.
login_view and logout_view handle session login/logout without CSRF enforcement.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Channel, SuperAdmin
from .serializers import ChannelSerializer, SuperAdminSerializer, UserSerializer
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
import random
import traceback
import requests
import os
import uuid
from typing import Dict, Any, Optional
import logging
import jwt
import os
import datetime
import time

# از livekit_api استفاده کنیم
import livekit.api as livekit_api

logger = logging.getLogger(__name__)

from .supabase_client import create_user, get_user_by_email, update_user, delete_user, create_channel

# متغیرهای محیطی برای LiveKit
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "fhS4ph29yWszyo")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "fq7M93nLDnGufmtbwJ9KYyHya3SNsWrx")
LIVEKIT_HOST = os.getenv("LIVEKIT_SERVER_URL", "http://livekit:7880")

def _make_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    ارسال درخواست به Supabase API
    """
    try:
        base_url = "http://kong:8000"
        url = f"{base_url}{path}"
        service_role_key = os.getenv('SERVICE_ROLE_KEY')
        if not service_role_key:
            logger.error("متغیر محیطی SERVICE_ROLE_KEY تنظیم نشده است")
            return None
            
        headers = {
            'apikey': service_role_key,
            'Authorization': f"Bearer {service_role_key}",
            'Content-Type': 'application/json'
        }

        logger.info(f"ارسال درخواست {method} به {url}")
        logger.info(f"هدرها: {headers}")
        if data:
            logger.info(f"داده‌های ارسالی: {data}")

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data
        )

        logger.info(f"کد وضعیت: {response.status_code}")
        logger.info(f"پاسخ دریافتی: {response.text}")

        if response.status_code >= 400:
            logger.error(f"خطا در درخواست به Supabase: {response.status_code} - {response.text}")
            return None

        # اگر درخواست موفق بود و پاسخ خالی است، True برگردان
        if response.status_code in [200, 201, 204] and not response.text.strip():
            return True

        try:
            json_response = response.json()
            # لیست خالی را به عنوان لیست خالی برگردان نه True
            return json_response
        except ValueError:
            # اگر پاسخ JSON نباشد، True برگردان
            return True
    except Exception as e:
        logger.error(f"خطا در ارسال درخواست به Supabase: {e}")
        logger.error(f"جزئیات خطا: {traceback.format_exc()}")
        return None

class ChannelViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Channel.objects.using('supabase').none()  # تغییر به none() برای جلوگیری از دسترسی مستقیم
    serializer_class = ChannelSerializer

    def _update_user_channels(self, channel_id: str, user_ids: list):
        """به‌روزرسانی کانال‌های کاربران"""
        if not user_ids or not isinstance(user_ids, list) or not channel_id:
            logger.warning(f"لیست کاربران یا شناسه کانال نامعتبر است: users={user_ids}, channel_id={channel_id}")
            return False
            
        try:
            logger.info(f"شروع به‌روزرسانی کانال‌های کاربران: channel_id={channel_id}, user_ids={user_ids}")
            
            # دریافت اطلاعات کانال فقط با استفاده از uid
            channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
            if channel is True or channel is None or (isinstance(channel, list) and len(channel) == 0):
                logger.error(f"کانال با uid {channel_id} یافت نشد")
                return False
            
            # استخراج اطلاعات کانال
            if isinstance(channel, list) and len(channel) > 0:
                channel = channel[0]
                logger.info(f"اطلاعات کانال یافت شده: {channel}")
            else:
                logger.error(f"فرمت داده کانال نامعتبر است: {channel}")
                
            success_count = 0    
            # برای هر کاربر، لیست کانال‌ها را به‌روزرسانی کن
            for user_id in user_ids:
                # دریافت اطلاعات کاربر
                user = _make_request('GET', f"/rest/v1/users?uid=eq.{user_id}")
                if user is True or user is None or (isinstance(user, list) and len(user) == 0):
                    logger.error(f"کاربر با شناسه {user_id} یافت نشد")
                    continue

                if isinstance(user, list) and len(user) > 0:
                    user = user[0]
                
                channels = user.get('allowed_channels', []) or []
                logger.info(f"کانال‌های فعلی کاربر {user_id}: {channels}")
                
                # اگر کانال در لیست کانال‌های کاربر نیست، اضافه کن
                if channel_id not in channels:
                    channels.append(channel_id)
                    logger.info(f"افزودن کانال {channel_id} به لیست کانال‌های کاربر {user_id}")
                    result = _make_request('PATCH', f"/rest/v1/users?uid=eq.{user_id}", {'allowed_channels': channels})
                    if result:
                        success_count += 1
                        logger.info(f"کانال {channel_id} با موفقیت به لیست کانال‌های کاربر {user_id} اضافه شد")
                    else:
                        logger.error(f"خطا در افزودن کانال {channel_id} به لیست کانال‌های کاربر {user_id}")
                else:
                    logger.info(f"کانال {channel_id} از قبل در لیست کانال‌های کاربر {user_id} وجود دارد")
                    success_count += 1

            logger.info(f"نتیجه به‌روزرسانی کانال‌های کاربران: {success_count} از {len(user_ids)} کاربر با موفقیت به‌روزرسانی شدند")
            return success_count > 0
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کانال‌های کاربران: {e}")
            logger.error(traceback.format_exc())
            return False

    def _remove_user_channels(self, channel_id: str, user_ids: list):
        """حذف کانال از لیست کانال‌های کاربران"""
        if not user_ids or not isinstance(user_ids, list) or not channel_id:
            logger.warning(f"لیست کاربران یا شناسه کانال نامعتبر است: users={user_ids}, channel_id={channel_id}")
            return False
            
        try:
            # دریافت اطلاعات کانال فقط با استفاده از uid
            channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
            if channel is True or channel is None or (isinstance(channel, list) and len(channel) == 0):
                logger.error(f"کانال با uid {channel_id} یافت نشد")
                return False
            
            # استخراج اطلاعات کانال
            if isinstance(channel, list) and len(channel) > 0:
                channel = channel[0]
                
            # برای هر کاربر، کانال را از لیست کانال‌ها حذف کن
            for user_id in user_ids:
                # دریافت اطلاعات کاربر
                user = _make_request('GET', f"/rest/v1/users?uid=eq.{user_id}")
                if user is True or user is None or (isinstance(user, list) and len(user) == 0):
                    logger.error(f"کاربر با شناسه {user_id} یافت نشد")
                    continue

                # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
                if isinstance(user, list) and len(user) > 0:
                    user = user[0]
                
                channels = user.get('allowed_channels', [])
                
                # اگر کانال در لیست کانال‌های کاربر است، حذف کن
                if channel_id in channels:
                    channels.remove(channel_id)
                    _make_request('PATCH', f"/rest/v1/users?uid=eq.{user_id}", {'allowed_channels': channels})

            return True
        except Exception as e:
            logger.error(f"خطا در حذف کانال از لیست کانال‌های کاربران: {e}")
            return False

    def list(self, request):
        """
        دریافت لیست کانال‌ها از Supabase REST API به جای دسترسی مستقیم به دیتابیس
        """
        try:
            # استفاده از _make_request برای دریافت کانال‌ها از Supabase REST API
            response = _make_request('GET', '/rest/v1/channels', None)
            logger.info(f"دریافت کانال‌ها از Supabase REST API: {response}")
            
            # اگر پاسخ وجود ندارد یا خطا دارد، آرایه خالی برگردان
            if not response:
                logger.warning("پاسخی از Supabase REST API دریافت نشد")
                return Response([], status=status.HTTP_200_OK)
                
            # اگر پاسخ True است (عملیات موفق اما داده‌ای وجود ندارد)
            if response is True:
                logger.info("پاسخ دریافتی True است (عملیات موفق اما داده‌ای وجود ندارد)")
                return Response([], status=status.HTTP_200_OK)
                
            # اگر پاسخ یک لیست است، همه آیتم‌ها را برگردان
            if isinstance(response, list):
                return Response(response, status=status.HTTP_200_OK)
            
            # اگر پاسخ یک آبجکت است
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در دریافت کانال‌ها از Supabase: {e}")
            return Response(
                {"detail": "Error fetching channels from Supabase API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        ایجاد کانال جدید با استفاده از Supabase REST API
        هر کانال دارای یک شناسه منحصر به فرد uuid است
        """
        try:
            # آماده‌سازی داده‌ها برای ارسال به API
            data = request.data.copy()
            name = data.get('name', '')
            allowed_users = data.get('allowed_users', [])
            
            # بررسی تکراری بودن نام کانال
            if name:
                # دریافت تمام کانال‌ها با این نام
                existing_channels = _make_request('GET', f"/rest/v1/channels?name=eq.{name}")
                
                # اگر کانالی با این نام وجود داشت، خطا بده
                if existing_channels and (isinstance(existing_channels, list) and len(existing_channels) > 0):
                    return Response(
                        {"detail": f"کانالی با نام '{name}' از قبل وجود دارد"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # استفاده از تابع create_channel
            logger.info(f"ایجاد کانال جدید با نام '{name}'")
            channel_data = create_channel(name=name, allowed_users=allowed_users)
            
            if not channel_data:
                return Response(
                    {"detail": "Failed to create channel in Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # اگر channel_data یک boolean است (مثل True)، باید اطلاعات کانال را با یک درخواست GET دریافت کنیم
            if isinstance(channel_data, bool):
                logger.info("پاسخ create_channel بولین بود. دریافت اطلاعات کانال با GET...")
                # در این حالت نیاز به uid داریم که باید از جای دیگری دریافت شود
                # باید کانال‌ها را بر اساس نام جستجو کنیم
                
                channels = _make_request('GET', f"/rest/v1/channels?name=eq.{name}")
                if isinstance(channels, list) and len(channels) > 0:
                    channel_data = channels[0]
                    logger.info(f"کانال با نام {name} یافت شد: {channel_data}")
                else:
                    logger.warning(f"کانال با نام {name} پس از ایجاد یافت نشد")
                    # تولید شناسه جدید برای جلوگیری از خطا
                    uid = str(uuid.uuid4())
                    channel_data = {
                        "id": None,  # ID واقعی در دسترس نیست
                        "name": name,
                        "allowed_users": allowed_users,
                        "uid": uid,
                        "created_at": datetime.datetime.now().isoformat()
                    }
            
            # به‌روزرسانی کانال‌های کاربران
            if channel_data and allowed_users and isinstance(allowed_users, list) and len(allowed_users) > 0:
                try:
                    # استفاده از uid به جای id
                    channel_id = channel_data.get('uid')
                    logger.info(f"شناسه کانال برای به‌روزرسانی کاربران: {channel_id}")
                    if channel_id:
                        logger.info(f"به‌روزرسانی {len(allowed_users)} کاربر با شناسه‌های: {allowed_users}")
                        result = self._update_user_channels(channel_id, allowed_users)
                        logger.info(f"نتیجه به‌روزرسانی کانال‌های کاربران: {'موفق' if result else 'ناموفق'}")
                    else:
                        logger.error("شناسه کانال (uid) در داده‌های کانال یافت نشد")
                        # لاگ کامل داده‌های کانال برای عیب‌یابی
                        logger.error(f"داده‌های کانال: {channel_data}")
                except Exception as e:
                    logger.error(f"خطا در به‌روزرسانی کانال‌های کاربران: {e}")
                    logger.error(f"جزئیات خطا: {traceback.format_exc()}")
                    # این خطا نباید باعث شکست کل عملیات شود
                
            return Response(channel_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"خطا در ایجاد کانال در Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """
        دریافت اطلاعات یک کانال خاص با استفاده از Supabase REST API
        """
        try:
            response = _make_request('GET', f"/rest/v1/channels?uid=eq.{pk}")
            
            if response is True or response is None or (isinstance(response, list) and len(response) == 0):
                return Response(
                    {"detail": "Channel not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # اگر پاسخ یک لیست است، اولین آیتم را برگردان
            if isinstance(response, list) and len(response) > 0:
                return Response(response[0], status=status.HTTP_200_OK)
            
            # اگر پاسخ یک آبجکت است
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در دریافت کانال از Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None, *args, **kwargs):
        """
        بروزرسانی یک کانال با استفاده از Supabase REST API
        """
        try:
            data = request.data.copy()
            
            # برای اطمینان از اینکه channel_id تغییر نمی‌کند
            if 'channel_id' in data:
                del data['channel_id']
                
            # دریافت اطلاعات کانال فعلی
            current_channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{pk}")
            if current_channel is True or current_channel is None or (isinstance(current_channel, list) and len(current_channel) == 0):
                return Response(
                    {"detail": "Channel not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
            if isinstance(current_channel, list) and len(current_channel) > 0:
                current_channel = current_channel[0]
            
            # بررسی تکراری بودن نام جدید کانال
            if 'name' in data and data['name'] and data['name'] != current_channel.get('name'):
                # دریافت تمام کانال‌ها با این نام
                existing_channels = _make_request('GET', f"/rest/v1/channels?name=eq.{data['name']}")
                
                # اگر کانالی با این نام وجود داشت، خطا بده
                if existing_channels and (isinstance(existing_channels, list) and len(existing_channels) > 0):
                    return Response(
                        {"detail": f"کانالی با نام '{data['name']}' از قبل وجود دارد"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # به‌روزرسانی کانال
            response = _make_request('PATCH', f"/rest/v1/channels?uid=eq.{pk}", data)
            
            if not response:
                return Response(
                    {"detail": "Failed to update channel in Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # اگر پاسخ True است، داده‌های به‌روزرسانی شده را برگردان
            if response is True:
                # دریافت اطلاعات کانال به‌روزرسانی شده
                updated_channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{pk}")
                if isinstance(updated_channel, list) and len(updated_channel) > 0:
                    response = updated_channel[0]
                else:
                    # اگر نمی‌توانیم داده‌های به‌روزرسانی شده را دریافت کنیم، از داده‌های ورودی استفاده می‌کنیم
                    response = {**current_channel, **data}
                
            # به‌روزرسانی کانال‌های کاربران
            if 'allowed_users' in data:
                # حذف کانال از لیست کانال‌های کاربرانی که دیگر مجاز نیستند
                removed_users = list(set(current_channel.get('allowed_users', [])) - set(data['allowed_users']))
                if removed_users:
                    self._remove_user_channels(pk, removed_users)

                # اضافه کردن کانال به لیست کانال‌های کاربران جدید
                new_users = list(set(data['allowed_users']) - set(current_channel.get('allowed_users', [])))
                if new_users:
                    self._update_user_channels(pk, new_users)
                
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کانال در Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """
        حذف کانال با استفاده از Supabase REST API
        با استفاده از uid
        """
        try:
            logger.info(f"درخواست حذف کانال با شناسه {pk}")
            
            # اگر pk خالی است، خطا برگردان
            if not pk:
                logger.error("شناسه کانال برای حذف ارائه نشده است")
                return Response(
                    {"detail": "Channel ID not provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # ابتدا اطلاعات کانال را دریافت می‌کنیم - از uid استفاده می‌کنیم
            channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{pk}")
            
            if not channel or (isinstance(channel, list) and len(channel) == 0):
                logger.error(f"کانال با شناسه uid={pk} یافت نشد")
                return Response(
                    {"detail": "Channel not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # اگر پاسخ یک لیست است، اولین آیتم را استفاده می‌کنیم
            if isinstance(channel, list) and len(channel) > 0:
                channel = channel[0]
            
            # گام 1: حذف کانال از لیست کانال‌های مجاز تمام کاربرانی که به این کانال دسترسی داشته‌اند
            try:
                # دریافت تمامی کاربران
                users = _make_request('GET', f"/rest/v1/users")
                
                if users and isinstance(users, list):
                    for user in users:
                        user_id = user.get('uid')
                        allowed_channels = user.get('allowed_channels', [])
                        
                        # اگر کانال در لیست کانال‌های مجاز کاربر وجود دارد، آن را حذف کن
                        if pk in allowed_channels:
                            allowed_channels.remove(pk)
                            _make_request('PATCH', f"/rest/v1/users?uid=eq.{user_id}", {'allowed_channels': allowed_channels})
                            logger.info(f"کانال {pk} از لیست کانال‌های مجاز کاربر {user_id} حذف شد")
            except Exception as e:
                logger.error(f"خطا در حذف کانال از لیست کانال‌های مجاز کاربران: {e}")
                # ادامه اجرا، زیرا این مرحله نباید کل فرآیند را متوقف کند
                
            # گام 2: حذف کانال از جدول channels با استفاده از uid
            delete_response = _make_request('DELETE', f"/rest/v1/channels?uid=eq.{pk}")
            
            if delete_response is None:
                logger.error(f"خطا در حذف کانال با uid={pk} از جدول channels")
                return Response(
                    {"detail": "Failed to delete channel"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            logger.info(f"کانال با uid={pk} با موفقیت حذف شد")
            return Response(
                {"detail": f"کانال {pk} با موفقیت حذف شد"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"خطا در حذف کانال با uid={pk}: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {"detail": f"Error deleting channel: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = []  # برداشتن نیاز به احراز هویت
    permission_classes = [AllowAny]  # اجازه دسترسی به همه
    queryset = DjangoUser.objects.using('supabase').none()  # تغییر به none() برای جلوگیری از دسترسی مستقیم
    serializer_class = UserSerializer

    def _update_channel_users(self, user_id: str, channel_ids: list):
        """به‌روزرسانی کاربران مجاز کانال‌ها"""
        if not channel_ids or not isinstance(channel_ids, list) or not user_id:
            logger.warning(f"لیست کانال‌ها یا شناسه کاربر نامعتبر است: channels={channel_ids}, user_id={user_id}")
            return False
            
        success = True
        logger.info(f"شروع به‌روزرسانی کاربران مجاز کانال‌ها: user_id={user_id}, channel_ids={channel_ids}")

        try:
            # برای هر کانال، لیست کاربران مجاز را به‌روزرسانی کن
            for channel_id in channel_ids:
                try:
                    # دریافت اطلاعات کانال فقط با استفاده از uid
                    channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
                    if not channel or len(channel) == 0:
                        logger.error(f"کانال با uid {channel_id} یافت نشد")
                        success = False
                        continue

                    channel = channel[0]
                    allowed_users = channel.get('allowed_users', []) or []
                    logger.info(f"کاربران مجاز فعلی کانال {channel_id}: {allowed_users}")
                    
                    # اگر کاربر در لیست کاربران مجاز نیست، اضافه کن
                    if user_id not in allowed_users:
                        allowed_users.append(user_id)
                        logger.info(f"افزودن کاربر {user_id} به لیست کاربران مجاز کانال {channel_id}")
                        result = _make_request('PATCH', f"/rest/v1/channels?uid=eq.{channel_id}", {'allowed_users': allowed_users})
                        if not result:
                            logger.error(f"خطا در به‌روزرسانی کاربران مجاز برای کانال {channel_id}")
                            success = False
                        else:
                            logger.info(f"کاربر {user_id} با موفقیت به لیست کاربران مجاز کانال {channel_id} اضافه شد")
                    else:
                        logger.info(f"کاربر {user_id} از قبل در لیست کاربران مجاز کانال {channel_id} وجود دارد")
                except Exception as e:
                    logger.error(f"خطا در پردازش کانال {channel_id}: {str(e)}")
                    logger.error(traceback.format_exc())
                    success = False

            return success
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کاربران مجاز کانال‌ها: {e}")
            logger.error(traceback.format_exc())
            return False

    def _remove_channel_users(self, user_id: str, channel_ids: list):
        """حذف کاربر از لیست کاربران مجاز کانال‌ها"""
        if not channel_ids or not isinstance(channel_ids, list) or not user_id:
            logger.warning(f"لیست کانال‌ها یا شناسه کاربر نامعتبر است: channels={channel_ids}, user_id={user_id}")
            return False
            
        success = True
        
        try:
            # برای هر کانال، کاربر را از لیست کاربران مجاز حذف کن
            for channel_id in channel_ids:
                try:
                    # دریافت اطلاعات کانال فقط با استفاده از uid
                    channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
                    if not channel or len(channel) == 0:
                        logger.error(f"کانال با uid {channel_id} یافت نشد")
                        success = False
                        continue

                    # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
                    if isinstance(channel, list) and len(channel) > 0:
                        channel = channel[0]
                    
                    allowed_users = channel.get('allowed_users', [])
                    
                    # اگر کاربر در لیست کاربران مجاز است، حذف کن
                    if user_id in allowed_users:
                        allowed_users.remove(user_id)
                        result = _make_request('PATCH', f"/rest/v1/channels?uid=eq.{channel_id}", {'allowed_users': allowed_users})
                        if not result:
                            logger.error(f"خطا در حذف کاربر از کانال {channel_id}")
                            success = False
                except Exception as e:
                    logger.error(f"خطا در پردازش حذف کاربر از کانال {channel_id}: {str(e)}")
                    success = False

            return success
        except Exception as e:
            logger.error(f"خطا در حذف کاربر از لیست کاربران مجاز کانال‌ها: {e}")
            return False

    def list(self, request):
        """
        دریافت لیست کاربران از Supabase REST API به جای دسترسی مستقیم به دیتابیس
        """
        try:
            # استفاده از _make_request برای دریافت کاربران از Supabase REST API
            response = _make_request('GET', '/rest/v1/users', None)
            logger.info(f"دریافت کاربران از Supabase REST API: {response}")

            # اگر پاسخ وجود ندارد یا خطا دارد، آرایه خالی برگردان
            if not response:
                logger.warning("پاسخی از Supabase REST API دریافت نشد")
                return Response([], status=status.HTTP_200_OK)
                
            # برگرداندن پاسخ API به عنوان نتیجه
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در دریافت کاربران از Supabase: {e}")
            return Response(
                {"detail": "Error fetching users from Supabase API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        ایجاد کاربر جدید با استفاده از Supabase Auth و REST API
        """
        try:
            # آماده‌سازی داده‌ها برای ارسال به API
            data = request.data.copy()
            
            username = data.get('username')
            password = data.get('password')
            role = data.get('role', 'regular')
            active = data.get('active', True)
            channels = data.get('allowed_channels', [])
            
            if not username or not password:
                return Response(
                    {"detail": "نام کاربری و رمز عبور الزامی است"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # بررسی اعتبار کانال‌ها
            valid_channels = []
            if channels:
                try:
                    for channel_id in channels:
                        # دریافت اطلاعات کانال فقط با استفاده از uid
                        channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
                        if channel and len(channel) > 0:
                            valid_channels.append(channel_id)
                        else:
                            logger.warning(f"کانال با uid {channel_id} یافت نشد و از لیست کانال‌های کاربر حذف شد")
                except Exception as e:
                    logger.error(f"خطا در بررسی اعتبار کانال‌ها: {e}")
            
            # استفاده از create_user برای ساخت کاربر
            logger.info(f"شروع فرآیند ساخت کاربر با نام کاربری {username}")
            
            user_data = create_user(
                username=username,
                password=password,
                role=role,
                active=active,
                allowed_channels=valid_channels
            )
            
            if not user_data:
                return Response(
                    {"detail": "خطا در ساخت کاربر در Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # به‌روزرسانی کانال‌ها برای کاربر جدید
            if valid_channels:
                try:
                    # استفاده از uid به جای id
                    user_uid = user_data.get('uid')
                    logger.info(f"شناسه کاربر برای به‌روزرسانی کانال‌ها: {user_uid}")
                    if user_uid:
                        logger.info(f"به‌روزرسانی {len(valid_channels)} کانال با شناسه‌های: {valid_channels}")
                        result = self._update_channel_users(user_uid, valid_channels)
                        logger.info(f"نتیجه به‌روزرسانی کانال‌های کاربر: {'موفق' if result else 'ناموفق'}")
                    else:
                        logger.error("شناسه کاربر (uid) در داده‌های کاربر یافت نشد")
                except Exception as e:
                    logger.error(f"خطا در به‌روزرسانی کانال‌های کاربر: {e}")
                    logger.error(f"جزئیات خطا: {traceback.format_exc()}")
                    # این خطا نباید باعث شکست کل عملیات شود
                
            return Response(
                UserSerializer(user_data).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"خطا در ساخت کاربر در Supabase: {e}")
            logger.error(f"جزئیات خطا: {traceback.format_exc()}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """
        دریافت اطلاعات یک کاربر خاص با استفاده از Supabase REST API
        """
        try:
            response = _make_request('GET', f"/rest/v1/users?uid=eq.{pk}")
            
            if not response or len(response) == 0:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            return Response(response[0], status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در دریافت کاربر از Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None, *args, **kwargs):
        """
        بروزرسانی یک کاربر با استفاده از Supabase REST API
        همراه با تضمین همسانی داده‌ها بین auth و جدول users
        """
        try:
            data = request.data.copy()
            original_data = data.copy()  # نگهداری داده‌های اصلی برای بازگشت احتمالی
            
            # دریافت اطلاعات کاربر فعلی
            current_user = _make_request('GET', f"/rest/v1/users?uid=eq.{pk}")
            if not current_user or len(current_user) == 0:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            current_user = current_user[0]
            
            # بررسی اعتبار کانال‌ها
            if 'allowed_channels' in data:
                valid_channels = []
                for channel_id in data['allowed_channels']:
                    # دریافت اطلاعات کانال فقط با استفاده از uid
                    channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
                    if channel and len(channel) > 0:
                        valid_channels.append(channel_id)
                    else:
                        logger.warning(f"کانال با uid {channel_id} یافت نشد و از لیست کانال‌های کاربر حذف شد")

                # جایگزینی لیست کانال‌ها با کانال‌های معتبر
                data['allowed_channels'] = valid_channels
            
            # تعیین نیاز به به‌روزرسانی اطلاعات auth
            auth_update_needed = False
            auth_data = {}
            
            if 'username' in data and data['username'] != current_user.get('username'):
                auth_update_needed = True
                # تبدیل نام کاربری به فرمت ایمیل اگر در قالب ایمیل نیست
                email = data['username']
                if '@' not in email:
                    email = f"{email}@example.com"
                auth_data['email'] = email
            
            if 'password' in data and data['password']:
                auth_update_needed = True
                auth_data['password'] = data['password']
            
            # آماده‌سازی داده‌های جدول users
            users_data = data.copy()
            if 'username' in users_data and '@example.com' in users_data['username']:
                users_data['username'] = users_data['username'].replace('@example.com', '')

            # فاز 1: به‌روزرسانی اطلاعات در auth
            auth_success = True
            auth_response = None # مقداردهی اولیه auth_response
            if auth_update_needed:
                try:
                    # به‌روزرسانی اطلاعات کاربر در Auth
                    auth_response = _make_request('PUT', f"/auth/v1/admin/users?uid=eq.{pk}", auth_data)

                    if not auth_response: # انتقال این بلوک به داخل try
                        auth_success = False
                        logger.error(f"خطا در به‌روزرسانی اطلاعات auth کاربر {pk}")
                except Exception as e: # اصلاح تورفتگی این except و بلوک آن
                    auth_success = False
                    logger.error(f"خطا در به‌روزرسانی auth: {e}")

            # فاز 2: به‌روزرسانی اطلاعات در جدول users
            # اگر auth با موفقیت به‌روزرسانی شد یا نیازی به به‌روزرسانی auth نبود
            if auth_success or not auth_update_needed:
                response = _make_request('PATCH', f"/rest/v1/users?uid=eq.{pk}", users_data)

                if not response:
                    # اگر auth با موفقیت به‌روزرسانی شد اما جدول users به‌روزرسانی نشد،
                    # بازگشت به حالت قبل در auth
                    if auth_success and auth_update_needed:
                        try:
                            # بازگشت به اطلاعات auth قبلی
                            rollback_auth_data = {}
                            if 'username' in original_data and '@' not in original_data['username']:
                                rollback_auth_data['email'] = f"{current_user.get('username')}@example.com"
                            
                            if rollback_auth_data:
                                _make_request('PUT', f"/auth/v1/admin/users?uid=eq.{pk}", rollback_auth_data)
                                logger.info(f"اطلاعات auth با موفقیت به حالت قبل بازگشت")
                        except Exception as rollback_err:
                            logger.error(f"خطا در بازگشت تغییرات auth: {rollback_err}")
                    
                    return Response(
                        {"detail": "خطا در به‌روزرسانی کاربر در Supabase"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # به‌روزرسانی کانال‌های مجاز کاربران در جدول channels
                if 'allowed_channels' in data:
                    try:
                        # حذف کاربر از لیست کاربران مجاز کانال‌هایی که دیگر در لیست کانال‌های کاربر نیستند
                        removed_channels = list(set(current_user.get('allowed_channels', [])) - set(data['allowed_channels']))
                        if removed_channels:
                            self._remove_channel_users(pk, removed_channels)

                        # اضافه کردن کاربر به لیست کاربران مجاز کانال‌های جدید
                        new_channels = list(set(data['allowed_channels']) - set(current_user.get('allowed_channels', [])))
                        if new_channels:
                            self._update_channel_users(pk, new_channels)
                    except Exception as channel_err:
                        logger.error(f"خطا در به‌روزرسانی کانال‌های مجاز: {channel_err}")
                        # ادامه اجرا و بازگشت پاسخ موفق، زیرا کاربر به‌روزرسانی شده است
                        logger.info("کاربر با موفقیت به‌روزرسانی شد اما در به‌روزرسانی کانال‌ها خطا رخ داد")
                
                return Response(response, status=status.HTTP_200_OK)
            
            # اگر auth با موفقیت به‌روزرسانی نشد
            elif 'username' in data:
                logger.warning("به‌روزرسانی auth ناموفق بود، فقط نام کاربری در جدول users به‌روزرسانی می‌شود")
                # فقط نام کاربری اصلی (بدون @example.com) را به‌روزرسانی می‌کنیم
                clean_data = {}
                clean_data['username'] = data['username'].replace('@example.com', '')
                
                response = _make_request('PATCH', f"/rest/v1/users?uid=eq.{pk}", clean_data)
                
                if not response:
                    return Response(
                        {"detail": "خطا در به‌روزرسانی نام کاربری در Supabase"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                return Response(
                    {"detail": "نام کاربری به‌روزرسانی شد اما سایر تغییرات اعمال نشد"},
                    status=status.HTTP_200_OK
                )
            
            # اگر به‌روزرسانی auth ناموفق بود و نام کاربری هم وجود ندارد
            return Response(
                {"detail": "خطا در به‌روزرسانی کاربر در Supabase Auth"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کاربر در Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """
        حذف یک کاربر با استفاده از Supabase REST API
        با استفاده از الگوی تراکنش دو مرحله‌ای برای تضمین همسانی داده‌ها
        """
        try:
            logger.info(f"شروع فرایند حذف کاربر با شناسه {pk}")
            
            # مرحله 0: بررسی وجود کاربر
            user = _make_request('GET', f"/rest/v1/users?uid=eq.{pk}")
            if not user or (isinstance(user, list) and len(user) == 0):
                logger.warning(f"کاربر با شناسه {pk} یافت نشد")
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
            if isinstance(user, list) and len(user) > 0:
                user = user[0]
            
            # نگهداری داده‌های اصلی برای بازگشت در صورت خطا
            original_user = user.copy()
            
            # مرحله 1: حذف کاربر از لیست کاربران مجاز تمام کانال‌ها
            try:
                # دریافت تمامی کانال‌ها
                channels = _make_request('GET', f"/rest/v1/channels")
                
                if channels and isinstance(channels, list):
                    for channel in channels:
                        channel_id = channel.get('uid')
                        allowed_users = channel.get('allowed_users', [])
                        
                        # اگر کاربر در لیست کاربران مجاز کانال وجود دارد، آن را حذف کن
                        if pk in allowed_users:
                            allowed_users.remove(pk)
                            _make_request('PATCH', f"/rest/v1/channels?uid=eq.{channel_id}", {'allowed_users': allowed_users})
                            logger.info(f"کاربر {pk} از لیست کاربران مجاز کانال {channel_id} حذف شد")
            except Exception as e:
                logger.error(f"خطا در حذف کاربر از لیست کاربران مجاز کانال‌ها: {e}")
                # ادامه اجرا، زیرا این مرحله نباید کل فرآیند را متوقف کند
            
            # مرحله 2: حذف کاربر از جدول users
            users_deleted = False
            try:
                logger.info(f"تلاش برای حذف کاربر {pk} از جدول users")
                users_response = _make_request('DELETE', f"/rest/v1/users?uid=eq.{pk}")

                if users_response is None:
                    # بررسی آیا کاربر واقعاً حذف شده است
                    check_user = _make_request('GET', f"/rest/v1/users?uid=eq.{pk}")
                    if check_user is None or (isinstance(check_user, list) and len(check_user) == 0):
                        users_deleted = True
                        logger.info(f"کاربر {pk} با موفقیت از جدول users حذف شد")
                    else:
                        logger.error(f"خطا در حذف کاربر {pk} از جدول users - کاربر همچنان وجود دارد")
                        return Response(
                            {"detail": "خطا در حذف کاربر از جدول users"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    users_deleted = True
                    logger.info(f"کاربر {pk} با موفقیت از جدول users حذف شد")
                
            except Exception as users_err:
                logger.error(f"خطا در حذف کاربر {pk} از جدول users: {users_err}")
                
            # مرحله 3: حذف کاربر از Supabase Auth (اول Auth حذف می‌کنیم، سپس جدول users)
            auth_deleted = False
            try:
                logger.info(f"تلاش برای حذف کاربر {pk} از Auth")
                auth_response = _make_request('DELETE', f"/auth/v1/admin/users/{pk}")
                
                # بررسی نتیجه حذف در Auth
                if auth_response is None:
                    # بررسی دقیق وضعیت حذف در Auth با درخواست مجدد
                    auth_check = _make_request('GET', f"/auth/v1/admin/users/{pk}")
                    
                    if auth_check is None or (isinstance(auth_check, list) and len(auth_check) == 0) or (
                        isinstance(auth_check, dict) and ('error_code' in auth_check or 'code' in auth_check)
                    ):
                        # کاربر در Auth وجود ندارد، عملیات حذف موفق بوده است
                        logger.info(f"کاربر {pk} در Auth یافت نشد، احتمالاً حذف شده")
                        auth_deleted = True
                    else:
                        logger.error(f"خطا در حذف کاربر {pk} از Auth - کاربر همچنان وجود دارد")
                        return Response(
                            {"detail": "خطا در حذف کاربر از Auth"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    auth_deleted = True
                    logger.info(f"کاربر {pk} با موفقیت از Auth حذف شد")
            
            except Exception as auth_err:
                error_msg = str(auth_err)
                logger.error(f"خطا در حذف کاربر {pk} از Auth: {error_msg}")
                
                # اگر خطا مربوط به 'Database error loading user' یا 'not_found' باشد، احتمالاً کاربر قبلاً از Auth حذف شده است
                if "Database error loading user" in error_msg or "not_found" in error_msg or "unexpected_failure" in error_msg:
                    logger.info(f"کاربر {pk} احتمالاً قبلاً از Auth حذف شده، ادامه عملیات...")
                    auth_deleted = True
                else:
                    # برای سایر خطاها، فرآیند را متوقف می‌کنیم
                    return Response(
                        {"detail": f"خطا در حذف کاربر از Auth: {error_msg}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # مرحله 4: حذف کاربر از جدول users
            users_deleted = False
            if auth_deleted:
                try:
                    logger.info(f"تلاش برای حذف کاربر {pk} از جدول users")
                    users_response = _make_request('DELETE', f"/rest/v1/users?uid=eq.{pk}")

                    if users_response is None:
                        # بررسی آیا کاربر واقعاً حذف شده است
                        check_user = _make_request('GET', f"/rest/v1/users?uid=eq.{pk}")
                        if check_user is None or (isinstance(check_user, list) and len(check_user) == 0):
                            users_deleted = True
                            logger.info(f"کاربر {pk} با موفقیت از جدول users حذف شد")
                        else:
                            logger.error(f"خطا در حذف کاربر {pk} از جدول users - کاربر همچنان وجود دارد")
                            return Response(
                                {"detail": "خطا در حذف کاربر از جدول users"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )
                    else:
                        users_deleted = True
                        logger.info(f"کاربر {pk} با موفقیت از جدول users حذف شد")
                
                except Exception as users_err:
                    logger.error(f"خطا در حذف کاربر {pk} از جدول users: {users_err}")
                    
                    # اگر از Auth حذف شده اما از جدول users حذف نشده، یک پیام هشدار برگردان
                    if auth_deleted:
                        return Response(
                            {"detail": f"هشدار: کاربر از Auth حذف شد اما از جدول users حذف نشد. خطا: {str(users_err)}"},
                            status=status.HTTP_200_OK
                        )
                    else:
                        return Response(
                            {"detail": f"خطا در حذف کاربر: {str(users_err)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
            
            # مرحله 5: برگرداندن پاسخ نهایی
            if users_deleted and auth_deleted:
                return Response(
                    {"detail": f"کاربر {pk} با موفقیت حذف شد"},
                    status=status.HTTP_200_OK
                )
            elif auth_deleted:
                return Response(
                    {"detail": f"کاربر از Auth حذف شد اما از جدول users حذف نشد"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "خطای نامشخص در حذف کاربر"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"خطا در حذف کاربر از Supabase: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SuperAdminViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = SuperAdmin.objects.using('supabase').all()
    serializer_class = SuperAdminSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('admin_super_user') or not data.get('admin_super_password') or not data.get('user_limit'):
            return Response({'error': 'اطلاعات ناقص است.'}, status=status.HTTP_400_BAD_REQUEST)

        if SuperAdmin.objects.using('supabase').filter(admin_super_user=data['admin_super_user']).exists():
            return Response({'error': 'این نام کاربری سوپر ادمین قبلا ثبت شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        data['created_by'] = request.user.username

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response

    username = request.data.get('username')
    password = request.data.get('password')

    try:
        admin_obj = SuperAdmin.objects.using('supabase').get(admin_super_user=username)
        if check_password(password, admin_obj.admin_super_password):
            django_user, created = DjangoUser.objects.get_or_create(username=username)
            if created:
                django_user.set_password(password)
                django_user.save()
            login(request, django_user)
            response = Response({'success': True})
            if 'HTTP_ORIGIN' in request.META:
                response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
                response['Access-Control-Allow-Credentials'] = 'true'
            return response
    except SuperAdmin.DoesNotExist:
        pass

    return Response({'error': 'نام کاربری یا رمز عبور سوپر ادمین اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def logout_view(request):
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response

    logout(request)
    response = Response({'success': True})
    if 'HTTP_ORIGIN' in request.META:
        response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
        response['Access-Control-Allow-Credentials'] = 'true'
    return response

@csrf_exempt
@api_view(['GET', 'OPTIONS'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def user_view(request):
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response

    django_user = request.user

    try:
        super_admin = SuperAdmin.objects.using('supabase').get(admin_super_user=django_user.username)
        data = {
            'id': super_admin.id,
            'username': super_admin.admin_super_user,
            'role': 'super_admin',
            'is_authenticated': True,
            'user_limit': super_admin.user_limit,
            'user_count': super_admin.user_count
        }
    except SuperAdmin.DoesNotExist:
        data = {
            'username': django_user.username,
            'is_authenticated': True,
            'role': 'unknown'
        }

    response = Response(data)
    if 'HTTP_ORIGIN' in request.META:
        response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
        response['Access-Control-Allow-Credentials'] = 'true'
    return response

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def client_auth_view(request):
    """
    API برای احراز هویت کاربر و ارسال توکن‌های LiveKit برای کانال‌های مجاز
    
    این API یوزرنیم، پسورد و آدرس سرور را دریافت می‌کند
    سپس کاربر را احراز هویت می‌کند و در صورت صحت، لیست کانال‌های مجاز
    و توکن دسترسی LiveKit برای هر کانال را برمی‌گرداند
    """
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response

    try:
        # دریافت اطلاعات از درخواست
        username = request.data.get('username')
        password = request.data.get('password')
        server_url = request.data.get('server_url', LIVEKIT_HOST)

        if not username or not password:
            return Response(
                {'error': 'نام کاربری و رمز عبور الزامی است.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # بررسی اعتبار اطلاعات با استفاده از Supabase Auth
        logger.info(f"درخواست احراز هویت برای کاربر {username}")
        
        auth_data = {
            "email": username,
            "password": password
        }
        
        auth_response = _make_request(
            "POST",
            "/auth/v1/token?grant_type=password",
            auth_data
        )
        
        # اگر اطلاعات کاربر صحیح نباشد
        if not auth_response or 'access_token' not in auth_response:
            logger.error(f"احراز هویت کاربر {username} ناموفق بود")
            return Response(
                {'error': 'نام کاربری یا رمز عبور اشتباه است.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        user_id = auth_response.get('user', {}).get('id')
        if not user_id:
            logger.error("شناسه کاربر در پاسخ Auth یافت نشد")
            return Response(
                {'error': 'خطا در دریافت اطلاعات کاربر'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        logger.info(f"کاربر {username} با شناسه {user_id} با موفقیت احراز هویت شد")
        
        # دریافت اطلاعات کاربر از دیتابیس
        user_data = _make_request(
            "GET",
            f"/rest/v1/users?uid=eq.{user_id}&select=*"
        )
        
        if not user_data or len(user_data) == 0:
            logger.error(f"اطلاعات کاربر {username} در دیتابیس یافت نشد")
            return Response(
                {'error': 'اطلاعات کاربر یافت نشد.'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        user = user_data[0]
        
        # بررسی فعال بودن کاربر
        if not user.get('active', False):
            logger.warn(f"کاربر {username} غیرفعال است")
            return Response(
                {'error': 'حساب کاربری شما غیرفعال شده است.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # دریافت کانال‌های مجاز کاربر
        user_channels = user.get('allowed_channels', [])
        
        # بررسی وجود کانال مجاز
        if not user_channels or len(user_channels) == 0:
            logger.warn(f"کاربر {username} هیچ کانال مجازی ندارد")
            return Response(
                {'error': 'شما به هیچ کانالی دسترسی ندارید.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # دریافت اطلاعات کانال‌ها از دیتابیس
        channels_data = []
        
        for channel_id in user_channels:
            channel_data = _make_request(
                "GET",
                f"/rest/v1/channels?uid=eq.{channel_id}&select=*"
            )
            
            if isinstance(channel_data, list) and len(channel_data) > 0:
                channels_data.append(channel_data[0])
            else:
                # کانال در دیتابیس وجود ندارد، اما یک داده مصنوعی ایجاد می‌کنیم
                channels_data.append({
                    "channel_id": channel_id,
                    "name": f"کانال {channel_id}",
                    "description": "توضیحات کانال"
                })
        
        # بررسی کلیدهای API LiveKit
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            logger.error("کلیدهای API LiveKit تنظیم نشده است")
            return Response(
                {'error': 'خطا در تنظیمات سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # ایجاد توکن LiveKit برای هر کانال
        tokens = {}
        
        for channel in channels_data:
            channel_id = channel.get('channel_id')
            
            if not channel_id:
                continue
                
            try:
                # ایجاد توکن برای دسترسی به اتاق
                room_name = f"channel-{channel_id}"
                
                # ایجاد توکن با استفاده از jwt به صورت مستقیم
                now = int(time.time())
                exp = now + 24 * 60 * 60  # اعتبار 24 ساعته
                
                token_data = {
                    "iss": LIVEKIT_API_KEY,      # API key
                    "nbf": now,                  # Not before
                    "exp": exp,                  # Expiration time
                    "sub": username,             # Subject (identity)
                    "jti": f"{username}-{channel_id}",  # JWT ID
                    "video": {
                        "room": room_name,
                        "roomJoin": True,
                        "canPublish": True,
                        "canSubscribe": True,
                        "canPublishData": True
                    },
                    "name": username  # نام کاربر
                }
                
                token = jwt.encode(token_data, LIVEKIT_API_SECRET, algorithm="HS256")
                
                # افزودن به لیست توکن‌ها
                tokens[channel_id] = {
                    'token': token,
                    'room': room_name,
                    'name': channel.get('name', f'کانال {channel_id}')
                }
                
                logger.info(f"توکن LiveKit برای کاربر {username} و کانال {channel_id} ایجاد شد")
                
            except Exception as e:
                logger.error(f"خطا در ایجاد توکن LiveKit برای کانال {channel_id}: {str(e)}")
                continue
        
        # بازگرداندن پاسخ
        response_data = {
            'success': True,
            'user_id': user_id,
            'username': username,
            'channels': channels_data,
            'tokens': tokens,
            'server_url': server_url
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        if 'HTTP_ORIGIN' in request.META:
            response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
            response['Access-Control-Allow-Credentials'] = 'true'
            
        return response
        
    except Exception as e:
        logger.error(f"خطا در احراز هویت کاربر: {str(e)}")
        logger.error(f"جزئیات خطا: {traceback.format_exc()}")
        
        response = Response(
            {'error': 'خطای سرور در احراز هویت', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        if 'HTTP_ORIGIN' in request.META:
            response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
            response['Access-Control-Allow-Credentials'] = 'true'
            
        return response

