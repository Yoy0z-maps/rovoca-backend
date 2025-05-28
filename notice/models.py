from django.db import models

# Create your models here.
class Notice(models.Model):
    title = models.TextField()
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.nickname}의 {self.name}"