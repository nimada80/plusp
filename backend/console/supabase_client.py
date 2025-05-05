import requests
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
import json
import logging

# تنظیم لاگر
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

BASE_URL = "http://kong:8000"
SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY")

if not SERVICE_ROLE_KEY:
    raise Exception("SERVICE_ROLE_KEY is missing!")

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
    "X-Client-Info": "supabase-js/1.0.0"
}

def _make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}"
    try:
        logger.info(f"ارسال درخواست {method} به {url}")
        logger.info(f"هدرها: {json.dumps(headers, ensure_ascii=False)}")
        if data:
            logger.info(f"داده‌های ارسالی: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.request(method, url, headers=headers, json=data)
        
        logger.info(f"کد وضعیت: {response.status_code}")
        logger.info(f"پاسخ دریافتی: {response.text}")
        
        if response.status_code >= 400:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"error": response.text}
                
            logger.error(f"خطا در درخواست: {response.status_code}")
            logger.error(f"متن خطا: {json.dumps(error_data, ensure_ascii=False)}")
            return None
            
        response.raise_for_status()
        
        # اگر پاسخ خالی است و درخواست موفق بود، True برگردان
        if response.status_code in [200, 201, 204] and not response.text.strip():
            logger.info("درخواست موفق اما پاسخ خالی")
            return True
            
        # برای درخواست‌های DELETE، اگر کد وضعیت 200 است و پاسخ خالی است، True برگردان
        if method == "DELETE" and response.status_code == 200:
            if not response.text.strip():
                logger.info("درخواست DELETE با موفقیت انجام شد")
                return True
            else:
                logger.error("پاسخ غیرمنتظره برای درخواست DELETE")
                return None
            
        result = response.json()
        logger.info(f"پاسخ پردازش شده: {json.dumps(result, ensure_ascii=False)}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در ارسال درخواست: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"متن پاسخ خطا: {json.dumps(error_data, ensure_ascii=False)}")
            except:
                logger.error(f"متن پاسخ خطا: {e.response.text}")
        return None

def create_user(email: str, password: str, role: str = 'user', active: bool = True, channels: list = None) -> Optional[Dict[str, Any]]:
    """
    ایجاد کاربر جدید در Supabase Auth
    """
    try:
        logger.info("شروع فرآیند ثبت کاربر جدید")
        logger.info(f"اطلاعات ورودی: email={email}, role={role}, active={active}, channels={channels}")
        
        # ساخت کاربر در Auth
        auth_data = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "role": role,
                "active": active,
                "channels": channels or []
            }
        }
        logger.info(f"داده‌های ارسالی به Auth: {auth_data}")
        
        auth_response = _make_request(
            "POST",
            "/auth/v1/admin/users",
            auth_data
        )
        
        if not auth_response:
            logger.error("خطا در ساخت کاربر در Auth")
            return None
            
        user_id = auth_response.get("id")
        if not user_id:
            logger.error("شناسه کاربر در پاسخ Auth یافت نشد")
            return None
            
        logger.info(f"کاربر با موفقیت در Auth ثبت شد. شناسه کاربر: {user_id}")
        logger.info(f"پاسخ کامل Auth: {auth_response}")
        
        return auth_response
    except Exception as e:
        logger.error(f"خطا در ساخت کاربر: {e}")
        logger.error(f"جزئیات خطا: {str(e)}")
        return None

def create_channel(name: str, channel_id: int, authorized_users: Optional[List[str]] = None) -> Dict[str, Any]:
    try:
        channel = {
            "name": name,
            "channel_id": channel_id,
            "authorized_users": authorized_users or []
        }
        
        response = _make_request(
            "POST",
            "/rest/v1/channels",
            channel
        )
        
        return response
    except Exception as e:
        print(f"خطا در ساخت کانال: {e}")
        return None

def get_user_by_email(email: str) -> Dict[str, Any]:
    try:
        response = _make_request(
            "GET",
            f"/rest/v1/users?username=eq.{email}&select=*"
        )
        return response[0] if response else None
    except Exception as e:
        print(f"خطا در دریافت اطلاعات کاربر: {e}")
        return None

def update_user(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = _make_request(
            "PATCH",
            f"/rest/v1/users?id=eq.{user_id}",
            data
        )
        return response
    except Exception as e:
        print(f"خطا در به‌روزرسانی کاربر: {e}")
        return None

def delete_user(user_id: str) -> bool:
    """
    حذف کاربر از هر دو جدول users و Supabase Auth
    """
    try:
        logger.info(f"شروع فرآیند حذف کاربر {user_id}")
        
        # حذف از جدول users
        logger.info(f"حذف کاربر {user_id} از جدول users")
        db_response = _make_request(
            "DELETE",
            f"/rest/v1/users?id=eq.{user_id}"
        )
        
        if db_response is None:
            logger.error(f"خطا در حذف کاربر {user_id} از جدول users")
            return False
            
        logger.info(f"کاربر {user_id} با موفقیت از جدول users حذف شد")
        
        # حذف از Supabase Auth
        logger.info(f"حذف کاربر {user_id} از Auth")
        auth_response = _make_request(
            "DELETE",
            f"/auth/v1/admin/users/{user_id}"
        )
        
        if auth_response is None:
            logger.error(f"خطا در حذف کاربر {user_id} از Auth")
            return False
            
        logger.info(f"کاربر {user_id} با موفقیت از Auth حذف شد")
        return True
    except Exception as e:
        logger.error(f"خطا در حذف کاربر {user_id}: {e}")
        return False