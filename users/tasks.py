# user/tasks.py

from django.utils import timezone as dj_timezone  # 수정
from datetime import timedelta
from django.db.models import Q
from .models import User
from word.models import Word
import requests
import random

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
    cutoff_date = dj_timezone.now().date() - timedelta(days=1)  # 24시간 기준
    users = (User.objects
             .filter(Q(last_active_date__lt=cutoff_date) | Q(last_active_date__isnull=True))
             .exclude(expo_push_token__isnull=True)
             .exclude(expo_push_token=""))
    for user in users:
        send_push_notification(user.expo_push_token, "ROVOCA", "오늘 하루 빠졌어요! 지금 들어와서 복습해요 📚")

def send_push_with_word():
    print("🚀 send_push_with_word() 실행됨")

    try:
        users = User.objects.exclude(expo_push_token__isnull=True).exclude(expo_push_token="")

        print(f"🔍 푸시 보낼 유저 수: {users.count()}")
        
        for user in users:
            print(f"📨 {user.username}에게 푸시 전송 시도 중...")
            
            # 사용자의 모든 단어 가져오기
            user_words = Word.objects.filter(wordbook__user=user)
            
            if not user_words.exists():
                # 단어가 없는 경우 기본 메시지
                title = "아직 등록된 단어가 없어요."
                message = "단어를 등록하고 학습을 시작하세요!"
            else:
                # 1/2 확률로 최근 단어 또는 오래된 단어 선택
                # if random.choice([True, False]):
                #     # 가장 최근 단어 (created_at 기준 내림차순)
                #     selected_word = user_words.order_by('-created_at').first()
                #     word_type = "최근"
                # else:
                #     # 가장 오래된 단어 (created_at 기준 오름차순)
                #     selected_word = user_words.order_by('created_at').first()
                #     word_type = "오래된"
                selected_word = user_words[random.randint(0, user_words.count() - 1)]
                
                # 선택된 단어의 첫 번째 의미 가져오기
                first_meaning = selected_word.meanings[0]['definition'] if selected_word.meanings else "의미 없음"
                
                title = f"{selected_word.text}의 뜻은 무엇일까요?"
                message = "기억이 나지 않는다면 지금 복습해요!"

            send_push_notification(
                user.expo_push_token,
                title,
                message
            )

    except Exception as e:
        print("❌ 예외 발생:", e)