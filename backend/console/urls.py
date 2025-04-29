"""
console/urls.py
Defines API routes for console app:
- login_view and logout_view for session auth
- ChannelViewSet and UserViewSet for channel/user CRUD operations
"""
from django.urls import path, include  # URL helpers
from rest_framework.routers import DefaultRouter
from . import views
from .views import login_view, logout_view

router = DefaultRouter()
router.register(r'channels', views.ChannelViewSet)  # Channel CRUD endpoints
router.register(r'users', views.UserViewSet)        # User CRUD endpoints

urlpatterns = [
    # Authentication endpoints (no CSRF/session requirement)
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    # ViewSet-generated routes for channels and users
    path('', include(router.urls)),
]
