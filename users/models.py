# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    # 상속 받은 필드 중 사용하지 않는 필드 제거
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    first_name = None
    last_name = None
    password = None

    social_id = models.CharField(max_length=128, unique=True)
    provider = models.CharField(max_length=16)  # google, apple, kakao 등
    nickname = models.CharField(max_length=128)
    profile_image = models.URLField(null=True, blank=True) # 추후 프로필 이미지 업로드 시 사용
    created_at = models.DateTimeField(auto_now_add=True)

    score = models.IntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    streak = models.IntegerField(default=0)

    USERNAME_FIELD = "social_id"
    REQUIRED_FIELDS = []  # createsuperuser 만들 때 꼭 있어야 함


    # 프로필 데이터를 문자열로 표현
    def __str__(self):
        return self.nickname
        
