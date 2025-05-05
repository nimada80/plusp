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
            # اگر پاسخ یک لیست خالی باشد، True برگردان
            if isinstance(json_response, list) and not json_response:
                return True
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
            # دریافت اطلاعات کانال
            channel = _make_request('GET', f"/rest/v1/channels?id=eq.{channel_id}")
            if channel is True or channel is None or (isinstance(channel, list) and len(channel) == 0):
                logger.error(f"کانال با شناسه {channel_id} یافت نشد")
                return False

            # برای هر کاربر، لیست کانال‌ها را به‌روزرسانی کن
            for user_id in user_ids:
                # دریافت اطلاعات کاربر
                user = _make_request('GET', f"/rest/v1/users?id=eq.{user_id}")
                if user is True or user is None or (isinstance(user, list) and len(user) == 0):
                    logger.error(f"کاربر با شناسه {user_id} یافت نشد")
                    continue

                user = user[0]
                channels = user.get('channels', [])
                
                # اگر کانال در لیست کانال‌های کاربر نیست، اضافه کن
                if channel_id not in channels:
                    channels.append(channel_id)
                    _make_request('PATCH', f"/rest/v1/users?id=eq.{user_id}", {'channels': channels})

            return True
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کانال‌های کاربران: {e}")
            return False

    def _remove_user_channels(self, channel_id: str, user_ids: list):
        """حذف کانال از لیست کانال‌های کاربران"""
        if not user_ids or not isinstance(user_ids, list) or not channel_id:
            logger.warning(f"لیست کاربران یا شناسه کانال نامعتبر است: users={user_ids}, channel_id={channel_id}")
            return False
            
        try:
            # برای هر کاربر، کانال را از لیست کانال‌ها حذف کن
            for user_id in user_ids:
                # دریافت اطلاعات کاربر
                user = _make_request('GET', f"/rest/v1/users?id=eq.{user_id}")
                if user is True or user is None or (isinstance(user, list) and len(user) == 0):
                    logger.error(f"کاربر با شناسه {user_id} یافت نشد")
                    continue

                # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
                if isinstance(user, list) and len(user) > 0:
                    user = user[0]
                
                channels = user.get('channels', [])
                
                # اگر کانال در لیست کانال‌های کاربر است، حذف کن
                if channel_id in channels:
                    channels.remove(channel_id)
                    _make_request('PATCH', f"/rest/v1/users?id=eq.{user_id}", {'channels': channels})

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
                
            # برگرداندن پاسخ API به عنوان نتیجه
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
        """
        try:
            # تولید یک شناسه تصادفی برای کانال
            while True:
                rand_id = random.randint(1000000, 9999999)
                # بررسی تکراری بودن شناسه
                existing = _make_request('GET', f"/rest/v1/channels?channel_id=eq.{rand_id}")
                # اگر پاسخ true باشد (بولین) یا لیست خالی باشد، شناسه تکراری نیست
                if existing is True or existing is None or (isinstance(existing, list) and len(existing) == 0):
                    break
                    
            # آماده‌سازی داده‌ها برای ارسال به API
            data = request.data.copy()
            data['channel_id'] = rand_id
            data['authorized_users'] = data.get('authorized_users', [])
            
            # ارسال درخواست به Supabase REST API
            logger.info(f"ارسال درخواست POST به http://kong:8000/rest/v1/channels")
            logger.info(f"داده‌های ارسالی: {data}")
            
            response = _make_request('POST', '/rest/v1/channels', data)
            
            if not response:
                return Response(
                    {"detail": "Failed to create channel in Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # اگر پاسخ True است، یعنی درخواست موفق بوده اما داده‌ای برگشت داده نشده
            # در این صورت، اطلاعات کانال را با یک درخواست GET دریافت می‌کنیم
            channel_data = None
            if response is True:
                logger.info("پاسخ POST موفقیت‌آمیز بود. دریافت اطلاعات کانال با GET...")
                channel_data = _make_request('GET', f"/rest/v1/channels?channel_id=eq.{rand_id}")
                if isinstance(channel_data, list) and len(channel_data) > 0:
                    channel_data = channel_data[0]
                else:
                    logger.info(f"دریافت اطلاعات کانال با GET نتیجه‌ای نداشت: {channel_data}")
                    # ایجاد یک پاسخ موفقیت‌آمیز ساختگی
                    channel_data = {
                        "id": None,  # ID واقعی در دسترس نیست
                        "channel_id": rand_id,
                        "name": data.get('name', ''),
                        "authorized_users": data.get('authorized_users', []),
                        "created_at": datetime.datetime.now().isoformat()
                    }
            else:
                # اگر پاسخ شیء است، از آن استفاده می‌کنیم
                channel_data = response

            # به‌روزرسانی کانال‌های کاربران
            if channel_data and 'authorized_users' in data and data['authorized_users'] and isinstance(data['authorized_users'], list):
                try:
                    channel_id = channel_data.get('id')
                    if channel_id:
                        self._update_user_channels(channel_id, data['authorized_users'])
                except Exception as e:
                    logger.error(f"خطا در به‌روزرسانی کانال‌های کاربران: {e}")
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
            response = _make_request('GET', f"/rest/v1/channels?id=eq.{pk}")
            
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
            current_channel = _make_request('GET', f"/rest/v1/channels?id=eq.{pk}")
            if current_channel is True or current_channel is None or (isinstance(current_channel, list) and len(current_channel) == 0):
                return Response(
                    {"detail": "Channel not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
            if isinstance(current_channel, list) and len(current_channel) > 0:
                current_channel = current_channel[0]
            
            # به‌روزرسانی کانال
            response = _make_request('PATCH', f"/rest/v1/channels?id=eq.{pk}", data)
            
            if not response:
                return Response(
                    {"detail": "Failed to update channel in Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # به‌روزرسانی کانال‌های کاربران
            if 'authorized_users' in data:
                # حذف کانال از لیست کانال‌های کاربرانی که دیگر مجاز نیستند
                removed_users = list(set(current_channel.get('authorized_users', [])) - set(data['authorized_users']))
                if removed_users:
                    self._remove_user_channels(pk, removed_users)

                # اضافه کردن کانال به لیست کانال‌های کاربران جدید
                new_users = list(set(data['authorized_users']) - set(current_channel.get('authorized_users', [])))
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
        حذف یک کانال با استفاده از Supabase REST API
        """
        try:
            # دریافت اطلاعات کانال
            channel = _make_request('GET', f"/rest/v1/channels?id=eq.{pk}")
            if channel is True or channel is None or (isinstance(channel, list) and len(channel) == 0):
                return Response(
                    {"detail": "Channel not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # اگر پاسخ یک لیست است، اولین آیتم را استفاده کن
            if isinstance(channel, list) and len(channel) > 0:
                channel = channel[0]
                
            # حذف کانال از لیست کانال‌های کاربران
            if 'authorized_users' in channel and channel['authorized_users']:
                self._remove_user_channels(pk, channel['authorized_users'])
                
            # حذف کانال
            response = _make_request('DELETE', f"/rest/v1/channels?id=eq.{pk}")
            
            if not response:
                return Response(
                    {"detail": "Failed to delete channel from Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"خطا در حذف کانال از Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = DjangoUser.objects.using('supabase').none()  # تغییر به none() برای جلوگیری از دسترسی مستقیم
    serializer_class = UserSerializer

    def _update_channel_users(self, user_id: str, channel_ids: list):
        """به‌روزرسانی کاربران مجاز کانال‌ها"""
        if not channel_ids or not isinstance(channel_ids, list) or not user_id:
            logger.warning(f"لیست کانال‌ها یا شناسه کاربر نامعتبر است: channels={channel_ids}, user_id={user_id}")
            return False
            
        success = True
        
        try:
            # برای هر کانال، لیست کاربران مجاز را به‌روزرسانی کن
            for channel_id in channel_ids:
                try:
                    # دریافت اطلاعات کانال
                    channel = _make_request('GET', f"/rest/v1/channels?id=eq.{channel_id}")
                    if not channel or len(channel) == 0:
                        logger.error(f"کانال با شناسه {channel_id} یافت نشد")
                        success = False
                        continue

                    channel = channel[0]
                    authorized_users = channel.get('authorized_users', [])
                    
                    # اگر کاربر در لیست کاربران مجاز نیست، اضافه کن
                    if user_id not in authorized_users:
                        authorized_users.append(user_id)
                        result = _make_request('PATCH', f"/rest/v1/channels?id=eq.{channel_id}", {'authorized_users': authorized_users})
                        if not result:
                            logger.error(f"خطا در به‌روزرسانی کاربران مجاز برای کانال {channel_id}")
                            success = False
                except Exception as e:
                    logger.error(f"خطا در پردازش کانال {channel_id}: {str(e)}")
                    success = False

            return success
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کاربران مجاز کانال‌ها: {e}")
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
                    # دریافت اطلاعات کانال
                    channel = _make_request('GET', f"/rest/v1/channels?id=eq.{channel_id}")
                    if not channel or len(channel) == 0:
                        logger.error(f"کانال با شناسه {channel_id} یافت نشد")
                        success = False
                        continue

                    channel = channel[0]
                    authorized_users = channel.get('authorized_users', [])
                    
                    # اگر کاربر در لیست کاربران مجاز است، حذف کن
                    if user_id in authorized_users:
                        authorized_users.remove(user_id)
                        result = _make_request('PATCH', f"/rest/v1/channels?id=eq.{channel_id}", {'authorized_users': authorized_users})
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
            channels = data.get('channels', [])
            
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
                        # بررسی وجود کانال
                        channel = _make_request('GET', f"/rest/v1/channels?id=eq.{channel_id}")
                        if not (channel is True or channel is None or (isinstance(channel, list) and len(channel) == 0)):
                            valid_channels.append(channel_id)
                        else:
                            logger.warning(f"کانال با شناسه {channel_id} یافت نشد و از لیست کانال‌های کاربر حذف شد")
                except Exception as e:
                    logger.error(f"خطا در بررسی اعتبار کانال‌ها: {e}")
            
            # استفاده از create_user برای ساخت کاربر
            logger.info(f"شروع فرآیند ساخت کاربر با نام کاربری {username}")
            
            user_data = create_user(
                username=username,
                password=password,
                role=role,
                active=active,
                channels=valid_channels
            )
            
            if not user_data:
                return Response(
                    {"detail": "خطا در ساخت کاربر در Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # به‌روزرسانی کانال‌ها برای کاربر جدید
            if valid_channels:
                try:
                    self._update_channel_users(user_data.get('id'), valid_channels)
                except Exception as e:
                    logger.error(f"خطا در به‌روزرسانی کانال‌های کاربر: {e}")
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
            response = _make_request('GET', f"/rest/v1/users?id=eq.{pk}")
            
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
        """
        try:
            data = request.data.copy()
            
            # دریافت اطلاعات کاربر فعلی
            current_user = _make_request('GET', f"/rest/v1/users?id=eq.{pk}")
            if not current_user or len(current_user) == 0:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            current_user = current_user[0]
            
            # بررسی اعتبار کانال‌ها
            if 'channels' in data:
                valid_channels = []
                for channel_id in data['channels']:
                    # بررسی وجود کانال
                    channel = _make_request('GET', f"/rest/v1/channels?id=eq.{channel_id}")
                    if channel and len(channel) > 0:
                        valid_channels.append(channel_id)
                    else:
                        logger.warning(f"کانال با شناسه {channel_id} یافت نشد و از لیست کانال‌های کاربر حذف شد")
                        
                # جایگزینی لیست کانال‌ها با کانال‌های معتبر
                data['channels'] = valid_channels
            
            # به‌روزرسانی کاربر
            response = _make_request('PATCH', f"/rest/v1/users?id=eq.{pk}", data)
            
            if not response:
                return Response(
                    {"detail": "Failed to update user in Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # به‌روزرسانی کاربران مجاز کانال‌ها
            if 'channels' in data:
                try:
                    # حذف کاربر از لیست کاربران مجاز کانال‌هایی که دیگر در لیست کانال‌های کاربر نیستند
                    removed_channels = list(set(current_user.get('channels', [])) - set(data['channels']))
                    if removed_channels:
                        self._remove_channel_users(pk, removed_channels)

                    # اضافه کردن کاربر به لیست کاربران مجاز کانال‌های جدید
                    new_channels = list(set(data['channels']) - set(current_user.get('channels', [])))
                    if new_channels:
                        self._update_channel_users(pk, new_channels)
                except Exception as channel_err:
                    logger.error(f"خطا در به‌روزرسانی کانال‌های مجاز: {channel_err}")
                    # ادامه اجرا و بازگشت پاسخ موفق، زیرا کاربر به‌روزرسانی شده است
                    logger.info("کاربر با موفقیت به‌روزرسانی شد اما در به‌روزرسانی کانال‌ها خطا رخ داد")

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کاربر در Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """
        حذف یک کاربر با استفاده از Supabase REST API
        """
        try:
            # دریافت اطلاعات کاربر
            user = _make_request('GET', f"/rest/v1/users?id=eq.{pk}")
            if not user or len(user) == 0:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            user = user[0]

            # حذف کاربر از لیست کاربران مجاز کانال‌ها
            if 'channels' in user:
                self._remove_channel_users(pk, user['channels'])

            # حذف کاربر
            response = _make_request('DELETE', f"/rest/v1/users?id=eq.{pk}")
            
            if not response:
                return Response(
                    {"detail": "Failed to delete user in Supabase"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"خطا در حذف کاربر از Supabase: {e}")
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
            f"/rest/v1/users?id=eq.{user_id}&select=*"
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
        user_channels = user.get('channels', [])
        
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
                f"/rest/v1/channels?channel_id=eq.{channel_id}&select=*"
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

