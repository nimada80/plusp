#!/usr/bin/env python
"""
اسکریپت تعمیر مجوزهای کانال

این اسکریپت مطمئن می‌شود که هر کانالی که کاربران را به عنوان کاربران مجاز دارد،
در لیست کانال‌های مجاز آن کاربران نیز قرار دارد.
"""

import os
import sys
import django
import logging
from typing import List, Dict, Any, Optional

# تنظیم متغیرهای محیطی برای دسترسی به پروژه جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()

from console.views import _make_request
from console.supabase_client import create_channel

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_user_channels(channel_id: str, user_ids: list) -> bool:
    """اضافه کردن کانال به لیست کانال‌های مجاز کاربران"""
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
        user_updated_count = 0
        for user_id in user_ids:
            # دریافت اطلاعات کاربر
            user = _make_request('GET', f"/rest/v1/users?uid=eq.{user_id}")
            if user is True or user is None or (isinstance(user, list) and len(user) == 0):
                logger.error(f"کاربر با شناسه {user_id} یافت نشد")
                continue

            user = user[0]
            channels = user.get('allowed_channels', [])
            
            # اگر کانال در لیست کانال‌های کاربر نیست، اضافه کن
            if channel_id not in channels:
                channels.append(channel_id)
                result = _make_request('PATCH', f"/rest/v1/users?uid=eq.{user_id}", {'allowed_channels': channels})
                if result:
                    user_updated_count += 1
                    logger.info(f"کانال {channel_id} به لیست کانال‌های مجاز کاربر {user_id} اضافه شد")
                else:
                    logger.error(f"خطا در به‌روزرسانی کانال‌های کاربر {user_id}")
            else:
                logger.info(f"کانال {channel_id} قبلاً در لیست کانال‌های مجاز کاربر {user_id} وجود دارد")

        logger.info(f"تعداد {user_updated_count} کاربر به‌روزرسانی شدند")
        return True
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی کانال‌های کاربران: {e}")
        return False


def fix_all_channels():
    """تعمیر دسترسی تمام کانال‌ها"""
    try:
        # دریافت تمام کانال‌ها
        channels = _make_request('GET', '/rest/v1/channels')
        
        if not channels or (isinstance(channels, list) and len(channels) == 0):
            logger.warning("هیچ کانالی یافت نشد")
            return False
            
        logger.info(f"تعداد {len(channels)} کانال یافت شد")
        
        # برای هر کانال، کاربران مجاز را به‌روزرسانی کن
        for channel in channels:
            channel_id = channel.get('uid')
            allowed_users = channel.get('allowed_users', [])
            
            if not channel_id:
                logger.warning(f"کانال بدون شناسه: {channel}")
                continue
                
            if not allowed_users or len(allowed_users) == 0:
                logger.info(f"کانال {channel_id} کاربر مجازی ندارد")
                continue
                
            logger.info(f"در حال به‌روزرسانی {len(allowed_users)} کاربر برای کانال {channel_id}")
            update_user_channels(channel_id, allowed_users)
            
        return True
    except Exception as e:
        logger.error(f"خطا در تعمیر دسترسی کانال‌ها: {e}")
        return False


def fix_specific_channel(channel_name: str):
    """تعمیر دسترسی یک کانال خاص با نام"""
    try:
        # دریافت کانال با نام مشخص
        channels = _make_request('GET', f"/rest/v1/channels?name=eq.{channel_name}")
        
        if not channels or (isinstance(channels, list) and len(channels) == 0):
            logger.warning(f"کانالی با نام {channel_name} یافت نشد")
            return False
            
        channel = channels[0]
        channel_id = channel.get('uid')
        allowed_users = channel.get('allowed_users', [])
            
        if not channel_id:
            logger.warning(f"کانال بدون شناسه: {channel}")
            return False
                
        if not allowed_users or len(allowed_users) == 0:
            logger.info(f"کانال {channel_id} کاربر مجازی ندارد")
            return False
                
        logger.info(f"در حال به‌روزرسانی {len(allowed_users)} کاربر برای کانال {channel_id}")
        return update_user_channels(channel_id, allowed_users)
    except Exception as e:
        logger.error(f"خطا در تعمیر دسترسی کانال: {e}")
        return False


if __name__ == "__main__":
    # اگر نام کانال مشخص شده باشد، فقط آن کانال را تعمیر کن
    if len(sys.argv) > 1:
        channel_name = sys.argv[1]
        logger.info(f"در حال تعمیر دسترسی‌های کانال '{channel_name}'...")
        result = fix_specific_channel(channel_name)
        if result:
            logger.info(f"تعمیر دسترسی‌های کانال '{channel_name}' با موفقیت انجام شد")
        else:
            logger.error(f"خطا در تعمیر دسترسی‌های کانال '{channel_name}'")
    else:
        # در غیر این صورت، تمام کانال‌ها را تعمیر کن
        logger.info("در حال تعمیر دسترسی‌های تمام کانال‌ها...")
        result = fix_all_channels()
        if result:
            logger.info("تعمیر دسترسی‌های تمام کانال‌ها با موفقیت انجام شد")
        else:
            logger.error("خطا در تعمیر دسترسی‌های کانال‌ها") 