# serializers.py

from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "social_id", "provider", "nickname", "profile_image", "created_at")
        read_only_fields = ("id", "social_id", "provider", "created_at")