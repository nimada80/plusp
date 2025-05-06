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
