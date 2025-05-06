from django.test import TestCase, Client
from unittest.mock import patch, MagicMock, call
import json
from django.urls import reverse
from rest_framework import status
from .views import ChannelViewSet

# Create your tests here.
class ChannelTestCase(TestCase):
    """آزمون‌های مربوط به عملکرد کانال‌ها"""
    
    @patch('console.views._make_request')
    @patch('console.views.create_channel')
    def test_channel_creation_updates_user_allowed_channels(self, mock_create_channel, mock_make_request):
        """
        تست این عملکرد که وقتی کانال جدید ایجاد می‌شود و کاربران مجاز به آن تخصیص می‌یابند،
        کانال به لیست کانال‌های مجاز آن کاربران هم اضافه می‌شود.
        """
        # شبیه‌سازی کاربران و کانال برای تست
        user1_id = "user1-uuid"
        user2_id = "user2-uuid"
        channel_id = "channel-uuid"
        
        # شبیه‌سازی پاسخ‌ها برای تابع create_channel
        mock_create_channel.return_value = {
            "name": "کانال تست",
            "uid": channel_id,
            "id": channel_id,
            "allowed_users": [user1_id, user2_id]
        }
        
        # شبیه‌سازی پاسخ‌ها برای تابع _make_request
        # وقتی اطلاعات کاربران خوانده می‌شود
        def mock_get_user(method, endpoint, data=None):
            if method == 'GET' and f"/rest/v1/users?uid=eq.{user1_id}" in endpoint:
                return [{"uid": user1_id, "username": "user1", "allowed_channels": []}]
            elif method == 'GET' and f"/rest/v1/users?uid=eq.{user2_id}" in endpoint:
                return [{"uid": user2_id, "username": "user2", "allowed_channels": []}]
            elif method == 'PATCH':
                return True
            else:
                return []
        
        mock_make_request.side_effect = mock_get_user
        
        # ایجاد یک Client برای ارسال درخواست
        client = Client()
        
        # شبیه‌سازی احراز هویت
        client.force_login = MagicMock()
        
        # از آنجا که channels-list در urls ممکن است تعریف نشده باشد، تست را به روش دیگری انجام می‌دهیم
        # به جای ارسال درخواست از طریق client، مستقیماً متد create را صدا می‌زنیم
        view = ChannelViewSet()
        
        # شبیه‌سازی request و kwargs
        request = MagicMock()
        request.data = {
            "name": "کانال تست",
            "allowed_users": [user1_id, user2_id]
        }
        view.request = request
        
        with patch('console.views.IsAuthenticated.has_permission', return_value=True):
            with patch('console.views.ChannelViewSet._update_user_channels') as mock_update_user_channels:
                # فراخوانی مستقیم متد create
                response = view.create(request)
                
                # بررسی فراخوانی تابع _update_user_channels
                mock_update_user_channels.assert_called_once_with(channel_id, [user1_id, user2_id])
                
    @patch('console.views._make_request')
    def test_update_user_channels_functionality(self, mock_make_request):
        """
        تست نحوه عملکرد تابع _update_user_channels برای اضافه کردن کانال به لیست کانال‌های مجاز کاربران
        """
        # شبیه‌سازی کاربران و کانال برای تست
        user1_id = "user1-uuid"
        user2_id = "user2-uuid"
        channel_id = "channel-uuid"
        
        # شبیه‌سازی پاسخ‌ها برای تابع _make_request
        def mock_api_request(method, endpoint, data=None):
            if method == 'GET' and endpoint == f"/rest/v1/channels?uid=eq.{channel_id}":
                return [{
                    "uid": channel_id,
                    "name": "کانال تست",
                    "allowed_users": [user1_id, user2_id]
                }]
            elif method == 'GET' and endpoint == f"/rest/v1/users?uid=eq.{user1_id}":
                return [{
                    "uid": user1_id, 
                    "username": "user1", 
                    "allowed_channels": []
                }]
            elif method == 'GET' and endpoint == f"/rest/v1/users?uid=eq.{user2_id}":
                return [{
                    "uid": user2_id, 
                    "username": "user2", 
                    "allowed_channels": ["other-channel"]
                }]
            elif method == 'PATCH':
                return True
            else:
                return []
        
        mock_make_request.side_effect = mock_api_request
        
        # ایجاد نمونه ChannelViewSet
        viewset = ChannelViewSet()
        
        # فراخوانی تابع _update_user_channels
        result = viewset._update_user_channels(channel_id, [user1_id, user2_id])
        
        # بررسی نتیجه
        self.assertTrue(result)
        
        # بررسی فراخوانی‌های _make_request
        expected_calls = [
            call('GET', f"/rest/v1/channels?uid=eq.{channel_id}"),
            call('GET', f"/rest/v1/users?uid=eq.{user1_id}"),
            call('PATCH', f"/rest/v1/users?uid=eq.{user1_id}", {'allowed_channels': [channel_id]}),
            call('GET', f"/rest/v1/users?uid=eq.{user2_id}"),
            call('PATCH', f"/rest/v1/users?uid=eq.{user2_id}", {'allowed_channels': ["other-channel", channel_id]})
        ]
        
        # بررسی تمام فراخوانی‌های مورد انتظار
        self.assertEqual(mock_make_request.call_args_list, expected_calls)
