"""
admin_panel/urls.py
Root URL configuration for the Django project:
- /admin/ → Django admin interface
- /api/   → API endpoints from console app
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin site
    path('admin/', admin.site.urls),
    # Console app API routes
    path('api/', include('console.urls')),
]
