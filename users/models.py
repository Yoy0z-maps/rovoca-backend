from django.db import models

# Create your models here.

class User(models.Model):
    social_id = models.CharField(max_length=128, unique=True)
    provider = models.CharField(max_length=16)  # google, apple, kakao 등
    nickname = models.CharField(max_length=128)
    profile_image = models.URLField(null=True, blank=True) # 추후 프로필 이미지 업로드 시 사용
    created_at = models.DateTimeField(auto_now_add=True)

    # 프로필 데이터를 문자열로 표현
    def __str__(self):
        return self.nickname
        
