from django.apps import AppConfig


class ConsoleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "console"
    verbose_name = "Console"

    def ready(self):
        """تنظیم ترتیب مدل‌ها در پنل ادمین"""
        # اجرا فقط در سرور اصلی (نه در کامندهای مدیریتی)
        import sys
        if 'runserver' not in sys.argv and 'gunicorn' not in sys.argv[0]:
            return
            
        # از استفاده از unregister که باعث خطا می‌شود، خودداری می‌کنیم
        # به جای آن، روش دیگری برای تغییر نام‌ها و ترتیب مدل‌ها استفاده می‌کنیم
        
        # تنظیمات نام و ترتیب مدل‌ها
        from django.contrib import admin
        from django.contrib.admin.sites import AlreadyRegistered

        # تنظیم verbose_name برای مدل‌ها که روی ترتیب نمایش و نام فیلدها تأثیر می‌گذارد
        from django.apps import apps
        try:
            app_config = apps.get_app_config('console')
            if hasattr(app_config, 'models_module'):
                # تنظیم متای مدل‌ها
                if hasattr(app_config.models_module, 'SuperAdmin'):
                    app_config.models_module.SuperAdmin._meta.verbose_name = "Super Admin"
                    app_config.models_module.SuperAdmin._meta.verbose_name_plural = "Super Admins"
                if hasattr(app_config.models_module, 'User'):
                    app_config.models_module.User._meta.verbose_name = "User"
                    app_config.models_module.User._meta.verbose_name_plural = "Users"
                if hasattr(app_config.models_module, 'Channel'):
                    app_config.models_module.Channel._meta.verbose_name = "Channel"
                    app_config.models_module.Channel._meta.verbose_name_plural = "Channels"
        except Exception as e:
            print(f"Error setting verbose names: {e}")
