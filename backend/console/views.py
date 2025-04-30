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
from .models import Channel, User
from .serializers import ChannelSerializer, UserSerializer
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
            data['password'] = make_password(data['password'])
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Handle user update: if password provided, hash it before updating record
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        
        # اگر رمز عبور در داده‌های ورودی باشد، آن را هش می‌کنیم
        if 'password' in data:
            data['password'] = make_password(data['password'])
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate user credentials and start a session. Returns success flag."""
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
    
    # معتبرسازی مستقیم از مدل User با بانک اطلاعاتی supabase
    try:
        user_obj = User.objects.using('supabase').get(username=username)
        if check_password(password, user_obj.password):
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
    except User.DoesNotExist:
        pass  # کاربر پیدا نشد، خطا برگردانده می‌شود
    
    return Response({'error': 'نام کاربری یا رمز عبور اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)

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
    
    # Try to get console User model corresponding to authenticated user
    try:
        user = User.objects.using('supabase').get(username=django_user.username)
        data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'is_authenticated': True
        }
    except User.DoesNotExist:
        data = {
            'username': django_user.username,
            'is_authenticated': True
        }
    
    response = Response(data)
    # Add CORS headers explicitly to the response
    if 'HTTP_ORIGIN' in request.META:
        response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
        response['Access-Control-Allow-Credentials'] = 'true'
    return response
