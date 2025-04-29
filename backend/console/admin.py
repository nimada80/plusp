from django.contrib import admin
from .models import Channel, User

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id')
    search_fields = ('name', 'channel_id')

class AllowedChannelsInline(admin.TabularInline):
    model = Channel.authorized_users.through
    fk_name = 'user'
    extra = 1

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'active')
    list_filter = ('role', 'active')
    search_fields = ('username',)
    inlines = [AllowedChannelsInline]
