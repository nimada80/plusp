"""
admin_panel/urls.py
Root URL configuration for the Django project:
- /admin/ → Django admin interface
- /api/   → API endpoints from console app
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt
from .admin_views import AdminLoginView

# استفاده از ویو سفارشی برای صفحه لاگین ادمین
admin.site.login_template = 'admin/login.html'
admin.site.login = AdminLoginView.as_view()

urlpatterns = [
    # Django admin site
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/', admin.site.urls),
    # Console app API routes
    path('api/', include('console.urls')),
]
