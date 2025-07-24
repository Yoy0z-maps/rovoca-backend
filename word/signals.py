from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User
from .models import Wordbook


@receiver(post_save, sender=User)
def create_default_wordbook(sender, instance, created, **kwargs):
    """
    새로운 사용자가 생성될 때 기본 워드북을 생성합니다.
    """
    if created:
        Wordbook.objects.create(
            user=instance,
            name="Default",
            description="Default Voca Bookcase",
            image="rovoca/default.jpg"
        ) 