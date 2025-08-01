# user/tasks.py

from django.utils import timezone
from datetime import timedelta
from .models import User
import requests

def send_push_notification(token, title, body):
    payload = {
        'to': token,
        'title': title,
        'body': body,
        'sound': 'default'
    }
    headers = {
        'Content-Type': 'application/json'
    }
    requests.post('https://exp.host/--/api/v2/push/send', json=payload, headers=headers)

def send_push_to_all_users():
    users = User.objects.exclude(expo_push_token__isnull=True).exclude(expo_push_token="")
    for user in users:
        send_push_notification(user.expo_push_token, "ROVOCA", "오늘의 단어 복습 해보세요!")

def send_push_to_inactive_users():
    now = timezone.now()
    threshold = now - timedelta(hours=24)
    users = User.objects.filter(last_active_at__lt=threshold).exclude(expo_push_token__isnull=True).exclude(expo_push_token="")
    for user in users:
        send_push_notification(user.expo_push_token, "ROVOCA", "오늘 하루 빠졌어요! 지금 들어와서 복습해요 📚")