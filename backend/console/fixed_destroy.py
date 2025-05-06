            # مرحله 3: حذف کاربر از Supabase Auth
            auth_deleted = False
            try:
                auth_response = _make_request('DELETE', f"/auth/v1/admin/users?uid=eq.{pk}")
                
                if not auth_response:
                    # بررسی دقیق وضعیت حذف در Auth
                    # درخواست دریافت کاربر را ارسال می‌کنیم تا ببینیم آیا کاربر هنوز در Auth وجود دارد یا خیر
                    auth_check = _make_request('GET', f"/auth/v1/admin/users?uid=eq.{pk}")
                    if auth_check is None or (isinstance(auth_check, list) and len(auth_check) == 0) or (isinstance(auth_check, dict) and 'error_code' in auth_check and auth_check['error_code'] == 'user_not_found'):
                        # کاربر در Auth وجود ندارد، بنابراین عملیات حذف موفق بوده است
                        logger.info(f"کاربر {pk} در Auth یافت نشد، احتمالاً قبلاً حذف شده")
                        auth_deleted = True
                    else:
                        # کاربر هنوز در Auth وجود دارد و حذف نشده است
                        logger.error(f"خطا در حذف کاربر {pk} از Auth - کاربر همچنان وجود دارد")
                        # اگر حذف از Auth با خطا مواجه شود اما از جدول users حذف شده باشد،
                        # باید کاربر را در جدول users بازگردانیم
                        if users_deleted:
                            try:
                                # بازگرداندن کاربر به جدول users
                                restore_user = {
                                    'uid': original_user.get('uid'),
                                    'username': original_user.get('username'),
                                    'role': original_user.get('role', 'regular'),
                                    'active': original_user.get('active', True),
                                    'allowed_channels': original_user.get('allowed_channels', [])
                                }
                                restore_response = _make_request('POST', f"/rest/v1/users", restore_user)
                                if restore_response:
                                    logger.info(f"کاربر {pk} با موفقیت به جدول users بازگردانده شد")
                                    # بازگرداندن ارتباطات کاربر با کانال‌ها
                                    if 'allowed_channels' in original_user and original_user['allowed_channels']:
                                        try:
                                            self._update_channel_users(pk, original_user['allowed_channels'])
                                            logger.info(f"ارتباطات کاربر {pk} با کانال‌ها با موفقیت بازگردانده شد")
                                        except Exception as restore_rel_err:
                                            logger.error(f"خطا در بازگشت ارتباطات کاربر {pk} با کانال‌ها: {restore_rel_err}")
                                else:
                                    logger.error(f"خطا در بازگرداندن کاربر {pk} به جدول users")
                            except Exception as restore_err:
                                logger.error(f"خطا در بازگرداندن کاربر {pk} به جدول users: {restore_err}")
                            return Response(
                                {"detail": f"کاربر از جدول users حذف شد اما حذف از Auth با خطا مواجه شد: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )
                else:
                    auth_deleted = True
                    logger.info(f"کاربر {pk} با موفقیت از Auth حذف شد")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"خطا در حذف کاربر {pk} از Auth: {error_msg}")
                # اگر خطا مربوط به 'Database error loading user' باشد، احتمالاً کاربر قبلاً از Auth حذف شده است
                if "Database error loading user" in error_msg or "unexpected_failure" in error_msg:
                    logger.info(f"کاربر {pk} احتمالاً قبلاً از Auth حذف شده، عملیات موفق تلقی می‌شود")
                    auth_deleted = True
                else:
                    # برای سایر خطاها، باید تراکنش را برگردانیم
                    # اگر حذف از Auth با خطا مواجه شود اما از جدول users حذف شده باشد،
                    # باید کاربر را در جدول users بازگردانیم
                    if users_deleted:
                        try:
                            # بازگرداندن کاربر به جدول users
                            restore_user = {
                                'uid': original_user.get('uid'),
                                'username': original_user.get('username'),
                                'role': original_user.get('role', 'regular'),
                                'active': original_user.get('active', True),
                                'allowed_channels': original_user.get('allowed_channels', [])
                            }
                            restore_response = _make_request('POST', f"/rest/v1/users", restore_user)
                            if restore_response:
                                logger.info(f"کاربر {pk} با موفقیت به جدول users بازگردانده شد")
                                # بازگرداندن ارتباطات کاربر با کانال‌ها
                                if 'allowed_channels' in original_user and original_user['allowed_channels']:
                                    try:
                                        self._update_channel_users(pk, original_user['allowed_channels'])
                                        logger.info(f"ارتباطات کاربر {pk} با کانال‌ها با موفقیت بازگردانده شد")
                                    except Exception as restore_rel_err:
                                        logger.error(f"خطا در بازگشت ارتباطات کاربر {pk} با کانال‌ها: {restore_rel_err}")
                            else:
                                logger.error(f"خطا در بازگرداندن کاربر {pk} به جدول users")
                        except Exception as restore_err:
                            logger.error(f"خطا در بازگرداندن کاربر {pk} به جدول users: {restore_err}")
                        return Response(
                            {"detail": f"کاربر از جدول users حذف شد اما حذف از Auth با خطا مواجه شد: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

            # اگر به هر دو مرحله (users و auth) با موفقیت انجام شود، پاسخ موفقیت بازگشت داده می‌شود
            if users_deleted and auth_deleted:
                return Response(
                    {"detail": f"کاربر {pk} با موفقیت حذف شد"},
                    status=status.HTTP_200_OK
                )
            elif users_deleted:
                return Response(
                    {"detail": f"کاربر از جدول users حذف شد اما عملیات در Auth با مشکل مواجه شد"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "خطای نامشخص در حذف کاربر"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                ) 