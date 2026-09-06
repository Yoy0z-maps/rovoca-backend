import logging
import random
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone as dj_timezone

import requests

from .models import User
from word.models import Word

logger = logging.getLogger(__name__)


def send_push_notification(token, title, body):
    payload = {
        'to': token,
        'title': title,
        'body': body,
        'sound': 'default',
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(
        'https://exp.host/--/api/v2/push/send',
        json=payload,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    logger.info("Expo push accepted with status=%s", response.status_code)


def send_push_to_all_users():
    try:
        users = User.objects.exclude(expo_push_token__isnull=True).exclude(expo_push_token="")

        logger.info("Sending review push to %s users", users.count())

        for user in users:
            send_push_notification(
                user.expo_push_token,
                "ROVOCA",
                "지금은 복습할 시간이에요!"
            )

    except Exception:
        logger.exception("Sending review pushes failed")

def send_push_to_inactive_users():
    cutoff_date = dj_timezone.now().date() - timedelta(days=1)  # 24시간 기준
    users = (User.objects
             .filter(Q(last_active_date__lt=cutoff_date) | Q(last_active_date__isnull=True))
             .exclude(expo_push_token__isnull=True)
             .exclude(expo_push_token=""))
    for user in users:
        send_push_notification(user.expo_push_token, "ROVOCA", "오늘 하루 빠졌어요! 지금 들어와서 복습해요 📚")

def send_push_with_word():
    try:
        users = User.objects.exclude(expo_push_token__isnull=True).exclude(expo_push_token="")

        logger.info("Sending vocabulary push to %s users", users.count())
        
        for user in users:
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

    except Exception:
        logger.exception("Sending vocabulary pushes failed")
