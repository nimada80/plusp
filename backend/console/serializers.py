"""
console/serializers.py
Defines Django REST framework serializers for User and Channel:
- UserSerializer: handles user data and channel memberships via 'channels'.
- ChannelSerializer: handles channel data and authorized_users assignment.
"""

from rest_framework import serializers
from .models import User, Channel

class UserSerializer(serializers.ModelSerializer):
    """Serialize User with ID, username, active, role, and channel membership."""
    # channels field links to Channel.allowed_channels relationship
    channels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Channel.objects.all(),
        source='allowed_channels'
    )
    class Meta:
        # Specifies model and fields to include in API
        model = User
        fields = ['id', 'username', 'active', 'role', 'channels']

class ChannelSerializer(serializers.ModelSerializer):
    """Serialize Channel with name, channel_id, and authorized user list."""
    # authorized_users field links to User model
    authorized_users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
    )
    class Meta:
        # Specifies model and fields to include in API
        model = Channel
        fields = ['id', 'name', 'channel_id', 'authorized_users']
