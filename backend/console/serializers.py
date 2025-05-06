"""
console/serializers.py
Defines Django REST framework serializers for User and Channel:
- UserSerializer: handles user data and channel memberships via 'allowed_channels'.
- ChannelSerializer: handles channel data and authorized_users assignment.
- SuperAdminSerializer: handles super admin data including credential and user limits.
"""

from rest_framework import serializers
from .models import User, Channel, SuperAdmin
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    """Serialize User with ID, username, active, role, and channel membership."""
    # allowed_channels field is a JSONField that stores a list of channel IDs
    allowed_channels = serializers.JSONField(required=False, default=list)
    # password field is write-only and required only for create operations
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        # Specifies model and fields to include in API
        model = User
        fields = ['uid', 'username', 'password', 'role', 'active', 'created_at', 'allowed_channels']
        # password should be write-only to avoid returning it in responses
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """Create a new user with validated data"""
        print(f"CREATE - IN SERIALIZER: {validated_data.get('password', 'No password')[:20]}...")  # Debug
        # password handled in views.py through create_user function
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update a user with validated data"""
        print(f"UPDATE - IN SERIALIZER: {validated_data.get('password', 'No password')[:20]}...")  # Debug
        
        # حذف فیلد password از validated_data اگر مقدار آن خالی یا undefined است
        if 'password' in validated_data and (validated_data['password'] is None or validated_data['password'] == '' or validated_data['password'] == 'undefined'):
            validated_data.pop('password')
        
        return super().update(instance, validated_data)

class ChannelSerializer(serializers.ModelSerializer):
    """Serialize Channel with name, uid, and authorized user list."""
    # allowed_users field is a JSONField that stores a list of user IDs
    allowed_users = serializers.JSONField(required=False, default=list)

    class Meta:
        # Specifies model and fields to include in API
        model = Channel
        fields = ['uid', 'name', 'allowed_users']

class SuperAdminSerializer(serializers.ModelSerializer):
    """Serialize SuperAdmin with all fields except admin_super_password for reading."""
    class Meta:
        model = SuperAdmin
        fields = ['id', 'admin_super_user', 'admin_super_password', 'user_limit', 'user_count', 'creation_date', 'created_by']
        extra_kwargs = {
            'admin_super_password': {'write_only': True},
            'created_by': {'read_only': True},
            'creation_date': {'read_only': True},
            'user_count': {'read_only': True}
        }
    
    def create(self, validated_data):
        """Hash password before creating super admin."""
        if 'admin_super_password' in validated_data:
            validated_data['admin_super_password'] = make_password(validated_data['admin_super_password'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Hash password before updating super admin if provided."""
        if 'admin_super_password' in validated_data:
            validated_data['admin_super_password'] = make_password(validated_data['admin_super_password'])
        return super().update(instance, validated_data)
