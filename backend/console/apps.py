from django.apps import AppConfig


class ConsoleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "console"
    verbose_name = "Console"

    def ready(self):
        """تنظیم ترتیب مدل‌ها در پنل ادمین"""
        from django.contrib import admin
        from . import models
        
        # تنظیم ترتیب نمایش مدل‌ها
        models_order = [
            models.SuperAdmin,
            models.User,
            models.Channel,
        ]
        
        # یک دیکشنری برای ذخیره مدل‌های ثبت شده
        registered_models = {}
        
        # ذخیره تمام مدل‌های ثبت شده
        for model, model_admin in admin.site._registry.items():
            if model._meta.app_label == self.name:
                registered_models[model] = model_admin
                admin.site.unregister(model)
        
        # ثبت مجدد مدل‌ها با ترتیب جدید
        for model in models_order:
            if model in registered_models:
                admin.site.register(model, registered_models[model].__class__)
