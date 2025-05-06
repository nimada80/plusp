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
            # دریافت اطلاعات کانال فقط با استفاده از uid
            channel = _make_request('GET', f"/rest/v1/channels?uid=eq.{channel_id}")
            if channel is True or channel is None or (isinstance(channel, list) and len(channel) == 0):
                logger.error(f"کانال با uid {channel_id} یافت نشد")
                return False
            
            # استخراج اطلاعات کانال
            if isinstance(channel, list) and len(channel) > 0:
                channel = channel[0]
                
            # برای هر کاربر، لیست کانال‌ها را به‌روزرسانی کن
            for user_id in user_ids:
                # دریافت اطلاعات کاربر
                user = _make_request('GET', f"/rest/v1/users?uid=eq.{user_id}")
                if user is True or user is None or (isinstance(user, list) and len(user) == 0):
                    logger.error(f"کاربر با شناسه {user_id} یافت نشد")
                    continue

                user = user[0]
                channels = user.get('allowed_users', [])
                
                # اگر کانال در لیست کانال‌های کاربر نیست، اضافه کن
                if channel_id not in channels:
                    channels.append(channel_id)
                    _make_request('PATCH', f"/rest/v1/users?uid=eq.{user_id}", {'allowed_users': channels})

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
                
                channels = user.get('allowed_users', [])
                
                # اگر کانال در لیست کانال‌های کاربر است، حذف کن
                if channel_id in channels:
                    channels.remove(channel_id)
                    _make_request('PATCH', f"/rest/v1/users?uid=eq.{user_id}", {'allowed_users': channels})

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
                uid = channel_data.get('uid') if isinstance(channel_data, dict) else None
                
                if uid:
                    channel_data = _make_request('GET', f"/rest/v1/channels?uid=eq.{uid}")
                    if isinstance(channel_data, list) and len(channel_data) > 0:
                        channel_data = channel_data[0]
                    else:
                        logger.info(f"دریافت اطلاعات کانال با GET نتیجه‌ای نداشت: {channel_data}")
                        # ایجاد یک پاسخ موفقیت‌آمیز ساختگی
                        channel_data = {
                            "id": None,  # ID واقعی در دسترس نیست
                            "name": name,
                            "allowed_users": allowed_users,
                            "uid": uid,
                            "created_at": datetime.datetime.now().isoformat()
                        }
                else:
                    logger.info("شناسه uid برای دریافت کانال موجود نیست")
                    channel_data = {
                        "id": None,
                        "name": name,
                        "allowed_users": allowed_users,
                        "uid": str(uuid.uuid4()),
                        "created_at": datetime.datetime.now().isoformat()
                    }

            # به‌روزرسانی کانال‌های کاربران
            if channel_data and 'allowed_users' in data and data['allowed_users'] and isinstance(data['allowed_users'], list):
                try:
                    channel_id = channel_data.get('id')
                    if channel_id:
                        self._update_user_channels(channel_id, data['allowed_users'])
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
                
