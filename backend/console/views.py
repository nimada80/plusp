"""
console/views.py
Defines REST API views for Channel and User management using Django REST framework.
ChannelViewSet and UserViewSet provide CRUD operations secured by session authentication and CSRF protection.
login_view and logout_view handle session login/logout without CSRF enforcement.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Channel, User, SuperAdmin
from .serializers import ChannelSerializer, UserSerializer, SuperAdminSerializer
from django.contrib.auth.hashers import make_password
import random
from rest_framework import viewsets, status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User as DjangoUser

class ChannelViewSet(viewsets.ModelViewSet):
    # ChannelViewSet: provides list, create, retrieve, update, destroy for Channel model
    # Requires authenticated user via Django session (SessionAuthentication)
    # Only logged-in users (IsAuthenticated) can access these endpoints
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Channel.objects.using('supabase').all()
    serializer_class = ChannelSerializer

    def create(self, request, *args, **kwargs):
        # Override create to generate a unique random channel_id before saving
        # تولید channel_id غیرتکراری
        while True:
            rand_id = random.randint(1000000, 9999999)
            if not Channel.objects.using('supabase').filter(channel_id=rand_id).exists():
                break
        request.data['channel_id'] = rand_id
        return super().create(request, *args, **kwargs)

class UserViewSet(viewsets.ModelViewSet):
    # UserViewSet: provides CRUD for console.User model
    # Ensures password is hashed on create/update and access requires authentication
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = User.objects.using('supabase').all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        # Handle user creation: validate input, check duplicates, hash password, then save
        data = request.data.copy()
        
        # بررسی داده‌های ورودی
        if not data.get('username') or not data.get('password') or not data.get('role'):
            return Response({'error': 'اطلاعات ناقص است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # بررسی تکراری نبودن نام کاربری
        if User.objects.using('supabase').filter(username=data['username']).exists():
            return Response({'error': 'این نام کاربری قبلا ثبت شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # هش کردن رمز عبور و استفاده از فیلد 'password'
        if 'password' in data:
            print(f"BEFORE HASHING: {data['password'][:3]}...")  # Debug - only show first few chars
            data['password'] = make_password(data['password'])
            print(f"AFTER HASHING: {data['password'][:20]}...")  # Debug
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # افزایش شمارنده تعداد کاربران در SuperAdmin
        try:
            super_admin = SuperAdmin.objects.using('supabase').first()
            if super_admin:
                super_admin.user_count += 1
                super_admin.save(using='supabase')
        except Exception as e:
            print(f"Error updating user count: {e}")
            
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Handle user update: if password provided, hash it before updating record
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        
        # اگر رمز عبور در داده‌های ورودی باشد، آن را هش می‌کنیم
        if 'password' in data:
            print(f"UPDATE - BEFORE HASHING: {data['password'][:3]}...")  # Debug
            data['password'] = make_password(data['password'])
            print(f"UPDATE - AFTER HASHING: {data['password'][:20]}...")  # Debug
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        # کاهش شمارنده تعداد کاربران در SuperAdmin
        try:
            super_admin = SuperAdmin.objects.using('supabase').first()
            if super_admin and super_admin.user_count > 0:
                super_admin.user_count -= 1
                super_admin.save(using='supabase')
        except Exception as e:
            print(f"Error updating user count: {e}")
            
        return super().destroy(request, *args, **kwargs)

class SuperAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SuperAdmin model.
    Provides CRUD operations for super admin credentials and user limits.
    Only accessible to authenticated users with proper permissions.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = SuperAdmin.objects.using('supabase').all()
    serializer_class = SuperAdminSerializer
    
    def create(self, request, *args, **kwargs):
        # Handle super admin creation with validation
        data = request.data.copy()
        
        # بررسی داده‌های ورودی
        if not data.get('admin_super_user') or not data.get('admin_super_password') or not data.get('user_limit'):
            return Response({'error': 'اطلاعات ناقص است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # بررسی تکراری نبودن نام کاربری سوپر ادمین
        if SuperAdmin.objects.using('supabase').filter(admin_super_user=data['admin_super_user']).exists():
            return Response({'error': 'این نام کاربری سوپر ادمین قبلا ثبت شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # اضافه کردن نام کاربر ایجاد کننده
        data['created_by'] = request.user.username
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate credentials against SuperAdmin and start a session. Returns success flag."""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response
    
    # Handle regular login
    username = request.data.get('username')
    password = request.data.get('password')
    
    # معتبرسازی از مدل SuperAdmin با بانک اطلاعاتی supabase
    try:
        # جستجوی نام کاربری در جدول SuperAdmin
        admin_obj = SuperAdmin.objects.using('supabase').get(admin_super_user=username)
        if check_password(password, admin_obj.admin_super_password):
            # اگر احراز هویت موفق بود، کاربر Django را پیدا یا ایجاد کنیم
            django_user, created = DjangoUser.objects.get_or_create(username=username)
            if created:
                django_user.set_password(password)
                django_user.save()
            
            # لاگین با کاربر Django
            login(request, django_user)
            response = Response({'success': True})
            
            # Add CORS headers explicitly to the response
            if 'HTTP_ORIGIN' in request.META:
                response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
                response['Access-Control-Allow-Credentials'] = 'true'
            return response
    except SuperAdmin.DoesNotExist:
        pass  # سوپر ادمین پیدا نشد، خطا برگردانده می‌شود
    
    return Response({'error': 'نام کاربری یا رمز عبور سوپر ادمین اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def logout_view(request):
    """Terminate user session. Returns success flag."""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response
        
    logout(request)
    response = Response({'success': True})
    # Add CORS headers explicitly to the response
    if 'HTTP_ORIGIN' in request.META:
        response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
        response['Access-Control-Allow-Credentials'] = 'true'
    return response

@csrf_exempt
@api_view(['GET', 'OPTIONS'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def user_view(request):
    """Return current authenticated user info."""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = Response()
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Content-Length'] = '0'
        return response
    
    # Django user model info
    django_user = request.user
    
    # Try to get SuperAdmin model corresponding to authenticated user
    try:
        super_admin = SuperAdmin.objects.using('supabase').get(admin_super_user=django_user.username)
        data = {
            'id': super_admin.id,
            'username': super_admin.admin_super_user,
            'role': 'super_admin',  # نقش سوپر ادمین
            'is_authenticated': True,
            'user_limit': super_admin.user_limit,
            'user_count': super_admin.user_count
        }
    except SuperAdmin.DoesNotExist:
        # سوپر ادمین پیدا نشد، اطلاعات ساده ارسال می‌شود
        data = {
            'username': django_user.username,
            'is_authenticated': True,
            'role': 'unknown'
        }
    
    response = Response(data)
    # Add CORS headers explicitly to the response
    if 'HTTP_ORIGIN' in request.META:
        response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
        response['Access-Control-Allow-Credentials'] = 'true'
    return response
