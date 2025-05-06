            if 'username' in users_data and '@example.com' in users_data['username']:
                users_data['username'] = users_data['username'].replace('@example.com', '')
            
            # فاز 1: به‌روزرسانی اطلاعات در auth
            auth_success = True
            if auth_update_needed:
                try:
                    # به‌روزرسانی اطلاعات کاربر در Auth
                    auth_response = _make_request('PUT', f"/auth/v1/admin/users/{pk}", auth_data)

                    if not auth_response:
                        auth_success = False
                        logger.error(f"خطا در به‌روزرسانی اطلاعات auth کاربر {pk}")
                except Exception as auth_err:
                    auth_success = False
                    logger.error(f"خطا در به‌روزرسانی auth: {auth_err}")
            
            # فاز 2: به‌روزرسانی اطلاعات در جدول users
            # اگر auth با موفقیت به‌روزرسانی شد یا نیازی به به‌روزرسانی auth نبود
            if auth_success or not auth_update_needed:
                response = _make_request('PATCH', f"/rest/v1/users?id=eq.{pk}", users_data)
