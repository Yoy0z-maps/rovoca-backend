# user/tasks.py

from django.utils import timezone
from datetime import timedelta
from .models import User
import requests

def send_push_notification(token, title, body):
    print(f"➡️ 푸시 요청 보내는 중: {token}")

    payload = {
        'to': token,
        'title': title,
        'body': body,
        'sound': 'default',
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post('https://exp.host/--/api/v2/push/send', json=payload, headers=headers)
    print("📦 Expo 응답:", response.status_code, response.json())


def send_push_to_all_users():
    print("🚀 send_push_to_all_users() 실행됨")

    try:
        users = User.objects.exclude(expo_push_token__isnull=True).exclude(expo_push_token="")

        print(f"🔍 푸시 보낼 유저 수: {users.count()}")

        for user in users:
            print(f"📨 {user.username}에게 푸시 전송 시도 중...")

            send_push_notification(
                user.expo_push_token,
                "ROVOCA",
                "지금은 복습할 시간이에요!"
            )

    except Exception as e:
        print("❌ 예외 발생:", e)

def send_push_to_inactive_users():
    now = timezone.now()
    threshold = now - timedelta(hours=24)
    users = User.objects.filter(last_active_at__lt=threshold).exclude(expo_push_token__isnull=True).exclude(expo_push_token="")
    for user in users:
        send_push_notification(user.expo_push_token, "ROVOCA", "오늘 하루 빠졌어요! 지금 들어와서 복습해요 📚")