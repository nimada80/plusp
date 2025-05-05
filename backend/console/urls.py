"""
console/urls.py
Defines API routes for console app:
- login_view and logout_view for session auth
- ChannelViewSet and UserViewSet for channel/user CRUD operations
- SuperAdminViewSet for managing superadmin credentials and user limits
- client_auth_view برای احراز هویت کاربر و ایجاد توکن LiveKit
"""
from django.urls import path, include  # URL helpers
from rest_framework.routers import DefaultRouter
from . import views
from .views import login_view, logout_view, user_view, client_auth_view
from .views import UserViewSet


router = DefaultRouter()
router.register(r'channels', views.ChannelViewSet)  # Channel CRUD endpoints
router.register(r'users', UserViewSet, basename='user')        # User CRUD endpoints
router.register(r'superadmins', views.SuperAdminViewSet)  # SuperAdmin CRUD endpoints

urlpatterns = [
    # Authentication endpoints (no CSRF/session requirement)
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/user/', user_view, name='user'),
    # مسیر جدید برای احراز هویت کاربر و ایجاد توکن LiveKit
    path('auth/client/', client_auth_view, name='client_auth'),
    # ViewSet-generated routes for channels and users
    path('', include(router.urls)),
]
