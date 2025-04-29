from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials are missing!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ساخت کاربر
def create_user(email: str, password: str, role: str = "user", active: bool = True, allowed_channels: Optional[List[int]] = None):
    try:
        # ثبت‌نام رسمی از طریق Supabase Auth
        response = supabase.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
        user_data = response.user
        user_id = user_data.id

        # درج سایر مشخصات در جدول users
        user_profile = {
            "id": user_id,
            "username": email,
            "role": role,
            "active": active,
            "allowed_channels": allowed_channels or []
        }
        supabase.table("users").insert(user_profile).execute()
        return user_data
    except Exception as e:
        print(f"خطا در ساخت کاربر: {e}")
        return None

# ساخت کانال
def create_channel(name: str, channel_id: int, authorized_users: Optional[List[str]] = None):
    try:
        channel = {
            "name": name,
            "channel_id": channel_id,
            "authorized_users": authorized_users or []
        }
        response = supabase.table("channels").insert(channel).execute()
        return response.data
    except Exception as e:
        print(f"خطا در ساخت کانال: {e}")
        return None