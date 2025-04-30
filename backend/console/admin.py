from django.contrib import admin
from .models import Channel, User, SuperAdmin
from django.contrib.auth.hashers import make_password

# مشخص کردن محتوای Inline
class AllowedChannelsInline(admin.TabularInline):
    model = Channel.authorized_users.through
    fk_name = 'user'
    extra = 1

# ثبت مدل SuperAdmin
@admin.register(SuperAdmin)
class SuperAdminAdmin(admin.ModelAdmin):
    list_display = ('super_admin_id', 'admin_super_user', 'user_limit', 'user_count')
    list_display_links = ('super_admin_id', 'admin_super_user')
    readonly_fields = ('super_admin_id', 'user_count', 'creation_date', 'created_by')
    search_fields = ('admin_super_user', 'created_by')
    exclude = ('user_count', 'creation_date', 'created_by')
    fieldsets = (
        ('User Credentials', {
            'fields': ('admin_super_user', 'admin_super_password')
        }),
        ('Limitations', {
            'fields': ('user_limit',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        هش کردن پسورد قبل از ذخیره
        """
        if 'admin_super_password' in form.changed_data:
            obj.admin_super_password = make_password(obj.admin_super_password)
        # اضافه کردن نام کاربر ایجادکننده
        if not change:  # فقط هنگام ایجاد رکورد جدید
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)

# ثبت مدل User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'active')
    list_filter = ('role', 'active')
    search_fields = ('username',)
    inlines = [AllowedChannelsInline]

# ثبت مدل Channel
@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id')
    search_fields = ('name', 'channel_id')
