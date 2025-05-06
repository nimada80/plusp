"""
console/models.py
Defines ORM models for the console app:
- generate_unique_id: helper to produce a unique random integer for fields.
- Channel: model with auto-generated unique channel_id, name, and ManyToMany link to User.
- User: custom user model mapping to 'users' table with credentials and role.
- SuperAdmin: model for storing super admin credentials and user limits.
"""

from django.db import models
import uuid

import random
from django.db import models
from django.core.exceptions import ValidationError

MIN_ID = 1000000
MAX_ID = 9999999

def generate_unique_id(model, field_name):
    """
    Generate a random integer between MIN_ID and MAX_ID that is unique
    for the given model field (e.g. Channel.channel_id).
    """
    while True:
        value = random.randint(MIN_ID, MAX_ID)
        if not model.objects.filter(**{field_name: value}).exists():
            return value

class Channel(models.Model):
    """
    Channel model with:
    - channel_id: unique random integer identifier
    - name: channel display name
    - authorized_users: users permitted to access this channel
    - uid: unique identifier string
    """
    # Unique, non-editable random ID generated on save
    channel_id = models.PositiveIntegerField(unique=True, editable=False, null=False)
    # Human-readable channel name
    name = models.CharField(max_length=255)
    # Unique identifier string (added to match migration 0011)
    uid = models.CharField(max_length=50, unique=True, editable=False, null=True)
    # Many-to-many relation to console.User for access control
    authorized_users = models.ManyToManyField(
        'User', blank=True, related_name='channel_access'
    )

    def save(self, *args, **kwargs):
        # On first save, assign a unique channel_id
        if not self.channel_id:
            self.channel_id = generate_unique_id(Channel, 'channel_id')
        # Validate channel_id remains within defined bounds
        if not (MIN_ID <= self.channel_id <= MAX_ID):
            raise ValidationError(
                f'channel_id must be between {MIN_ID} and {MAX_ID}'
            )
        # Proceed with normal save
        super().save(*args, **kwargs)

    def __str__(self):
        # String representation returns channel name
        return self.name

class User(models.Model):
    """
    Custom user model stored in 'users' table:
    - uid: UUID primary key
    - username: unique login name
    - role: user role identifier
    - active: account status flag
    - created_at: timestamp of account creation
    - allowed_channels: list of channel UIDs
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=255, unique=True)
    role = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    allowed_channels = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return self.username

class SuperAdmin(models.Model):
    """
    Super Admin model for storing admin credentials and user limits:
    - id: primary key
    - super_admin_id: unique random identifier
    - admin_super_user: super admin username
    - admin_super_password: hashed super admin password
    - user_limit: maximum number of users allowed
    - user_count: current number of users (default 0)
    - creation_date: when this super admin was created
    - created_by: username of the creator
    """
    id = models.BigAutoField(primary_key=True)
    super_admin_id = models.PositiveIntegerField(unique=True, editable=False, null=True)
    admin_super_user = models.CharField(max_length=150, unique=True, verbose_name="Super Admin name")
    admin_super_password = models.CharField(max_length=128, verbose_name="Super Admin password")
    user_limit = models.PositiveIntegerField(verbose_name="User Limit")
    user_count = models.PositiveIntegerField(default=0, verbose_name="User Count")
    creation_date = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=150)

    class Meta:
        db_table = 'super_admin'
        verbose_name = 'Super Admin'
        verbose_name_plural = 'Super Admins'

    def save(self, *args, **kwargs):
        # On first save, assign a unique super_admin_id
        if not self.super_admin_id:
            self.super_admin_id = generate_unique_id(SuperAdmin, 'super_admin_id')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.admin_super_user
