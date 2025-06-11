from django.db import models

# Create your models here.
import uuid
from django.db import models
from users.models import User

def wordbook_image_path(instance, filename):  
    return f'wordbook/{instance.user.id}/{filename}'

class Wordbook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wordbooks')
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=wordbook_image_path, default='rovoca/default.jpg')
    views = models.PositiveIntegerField(default=0) 

    @property
    def word_count(self):
        return self.words.count() 

    def __str__(self):
        return f"{self.user.nickname}의 {self.name}"

class Word(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wordbook = models.ForeignKey(Wordbook, on_delete=models.CASCADE, related_name='words')
    text = models.CharField(max_length=128)
    meanings = models.JSONField(default=list)  # 예: [{"part": "noun", "definition": "개", "example": "개는 개다."}]
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text