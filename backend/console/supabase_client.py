import requests
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
import json
import logging
import traceback
import datetime
import uuid

# تنظیم لاگر
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

_base_url = "http://kong:8000"
_api_key = os.getenv("SERVICE_ROLE_KEY")

if not _api_key:
    raise Exception("SERVICE_ROLE_KEY is missing!")

headers = {
    "apikey": _api_key,
    "Authorization": f"Bearer {_api_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
    "X-Client-Info": "supabase-js/1.0.0"
}

def _make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    url = f"{_base_url}{endpoint}"
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

def create_user(username: str, password: str, role: str = 'user', active: bool = True, allowed_channels: list = None) -> Optional[Dict[str, Any]]:
    """
    ایجاد کاربر جدید در Supabase Auth
    تبدیل نام کاربری به فرمت ایمیل با افزودن @example.com در صورت لزوم
    """
    auth_response = None
    try:
        logger.info("شروع فرآیند ثبت کاربر جدید")
        logger.info(f"اطلاعات ورودی: username={username}, role={role}, active={active}, allowed_channels={allowed_channels}")
        
        # تبدیل نام کاربری به فرمت ایمیل اگر در قالب ایمیل نیست
        email = username
        if '@' not in username:
            email = f"{username}@example.com"
            logger.info(f"نام کاربری به فرمت ایمیل تبدیل شد: {email}")
        
        # ساخت کاربر در Auth
        auth_data = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "role": role,
                "active": active,
                "allowed_channels": allowed_channels or [],
                "email_verified": True  # برای اجتناب از نیاز به تأیید ایمیل
            }
        }
        
        logger.info(f"داده‌های ارسالی به Auth: {auth_data}")
        
        headers = {
            "apikey": _api_key,
            "Authorization": f"Bearer {_api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
            "X-Client-Info": "supabase-js/1.0.0"
        }
        
        logger.info(f"ارسال درخواست POST به http://kong:8000/auth/v1/admin/users")
        logger.info(f"هدرها: {json.dumps(headers)}")
        logger.info(f"داده‌های ارسالی: {json.dumps(auth_data)}")
        
        response = requests.post(
            f"{_base_url}/auth/v1/admin/users",
            headers=headers,
            json=auth_data
        )
        
        logger.info(f"کد وضعیت: {response.status_code}")
        
        # اگر پاسخ خالی باشد یا کد وضعیت مناسب نباشد، خطا برمی‌گرداند
        if response.status_code != 200 and response.status_code != 201:
            logger.error(f"خطا در ساخت کاربر: {response.text}")
            return None
            
        try:
            auth_response = response.json()
            logger.info(f"پاسخ دریافتی: {response.text}")
            logger.info(f"پاسخ پردازش شده: {json.dumps(auth_response)}")
        except json.JSONDecodeError:
            logger.error("خطا در پردازش پاسخ JSON از Auth API")
            logger.error(f"محتوای پاسخ: {response.text}")
            auth_response = {"id": None, "email": email, "created_at": datetime.datetime.now().isoformat()}
        
        if not auth_response or "id" not in auth_response:
            logger.error("پاسخ Auth خالی است یا شناسه کاربر وجود ندارد")
            if response.text:
                logger.error(f"متن پاسخ: {response.text}")
            return None
            
        logger.info(f"کاربر با موفقیت در Auth ثبت شد. شناسه کاربر: {auth_response['id']}")
        logger.info(f"پاسخ کامل Auth: {auth_response}")
        
        # ذخیره کاربر در جدول users
        user_data = {
            "uid": auth_response["id"],
            "username": username,
            "role": role,
            "active": active,
            "allowed_channels": allowed_channels or []
        }
        
        logger.info(f"ارسال درخواست POST به http://kong:8000/rest/v1/users")
        logger.info(f"هدرها: {json.dumps(headers)}")
        logger.info(f"داده‌های ارسالی: {json.dumps(user_data)}")
        
        rest_response = requests.post(
            f"{_base_url}/rest/v1/users",
            headers=headers,
            json=user_data
        )
        
        logger.info(f"کد وضعیت: {rest_response.status_code}")
        
        # ذخیره موفقیت‌آمیز در جدول users
        if rest_response.status_code == 201 or rest_response.status_code == 200:
            try:
                rest_data = rest_response.json()
                logger.info(f"پاسخ دریافتی: {rest_response.text}")
                logger.info(f"پاسخ پردازش شده: {json.dumps(rest_data)}")
                logger.info("کاربر با موفقیت در جدول users ثبت شد")
                
                # اگر پاسخ یک لیست است، آیتم اول را برمی‌گرداند
                if isinstance(rest_data, list) and len(rest_data) > 0:
                    return rest_data[0]
                return rest_data
            except json.JSONDecodeError:
                logger.error("خطا در پردازش پاسخ JSON از REST API")
                # در صورت خطا در پردازش JSON، داده‌های کاربر را برمی‌گرداند
                return user_data
        else:
            # اگر ذخیره در جدول users با خطا مواجه شود، کاربر را از Auth حذف می‌کند
            logger.error(f"خطا در ذخیره کاربر در جدول users: {rest_response.text}")
            
            # حذف کاربر از Auth
            delete_response = requests.delete(
                f"{_base_url}/auth/v1/admin/users/{auth_response['id']}",
                headers=headers
            )
            
            logger.error(f"حذف کاربر از Auth: {delete_response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"خطا در ساخت کاربر: {e}")
        logger.error(f"جزئیات خطا: {traceback.format_exc()}")
        
        # اگر کاربر در Auth ساخته شده اما در جدول users با خطا مواجه شده، کاربر را از Auth حذف می‌کند
        if auth_response and "id" in auth_response:
            try:
                headers = {
                    "apikey": _api_key,
                    "Authorization": f"Bearer {_api_key}",
                    "Content-Type": "application/json"
                }
                
                delete_response = requests.delete(
                    f"{_base_url}/auth/v1/admin/users/{auth_response['id']}",
                    headers=headers
                )
                
                logger.error(f"حذف کاربر از Auth به دلیل خطا: {delete_response.status_code}")
            except Exception as delete_error:
                logger.error(f"خطا در حذف کاربر از Auth: {delete_error}")
        
        return None

def create_channel(name: str, allowed_users: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    ایجاد کانال جدید در Supabase
    با ساخت شناسه uid که با uuid باشد
    """
    try:
        logger.info(f"شروع فرآیند ایجاد کانال: name={name}")
        
        # ایجاد یک uid منحصر به فرد با استفاده از uuid
        unique_uid = str(uuid.uuid4())
        
        # داده‌های برای ارسال به API
        channel = {
            "name": name,
            "uid": unique_uid,
            "allowed_users": allowed_users or []
        }
        
        logger.info(f"داده‌های کانال ارسالی: {channel}")
        
        response = _make_request(
            "POST",
            "/rest/v1/channels",
            channel
        )
        
        if response is True:
            # اگر _make_request یک boolean برگرداند، به این معنی است که عملیات موفق بوده اما داده‌ای برگشت نداده
            logger.info("کانال با موفقیت ایجاد شد اما داده‌ای برگشت داده نشد")
            # دریافت اطلاعات کانال ایجاد شده
            created_channel = _make_request(
                "GET", 
                f"/rest/v1/channels?uid=eq.{unique_uid}"
            )
            
            if isinstance(created_channel, list) and len(created_channel) > 0:
                return created_channel[0]
            
            # ساخت یک پاسخ با حاوی اطلاعات اصلی کانال
            return {
                "success": True, 
                "message": "کانال با موفقیت ایجاد شد", 
                "uid": unique_uid,
                "name": name,
                "allowed_users": allowed_users or []
            }
            
        # اگر پاسخ None یا False باشد، یک پاسخ با حداقل اطلاعات برگشت می‌دهیم
        if response is None or response is False:
            logger.error("خطا در ایجاد کانال - پاسخ خالی یا نامعتبر")
            return None
            
        # اگر پاسخ یک لیست باشد، اولین آیتم را برگشت می‌دهیم
        if isinstance(response, list) and len(response) > 0:
            return response[0]
            
        return response
    except Exception as e:
        logger.error(f"خطا در ساخت کانال: {e}")
        logger.error(f"جزئیات خطا: {traceback.format_exc()}")
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
            f"/rest/v1/users?uid=eq.{user_id}",
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
            f"/rest/v1/users?uid=eq.{user_id}"
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