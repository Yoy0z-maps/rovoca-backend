# user/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .tasks import send_push_to_all_users, send_push_to_inactive_users, send_push_with_word
from pytz import timezone

# 전역 변수 초기화
_scheduler_started = False

def start():
    global _scheduler_started

    if _scheduler_started:
        print("스케줄러가 이미 실행 중입니다.")
        return

    scheduler = BackgroundScheduler(timezone=timezone("Asia/Seoul"))

    # 오전 8시 가장 오래된 / 최근 단어 알림
    scheduler.add_job(send_push_with_word, CronTrigger(hour=23, minute=8))

    # 오후 8시 전체 유저 복습 알림
    scheduler.add_job(send_push_to_all_users, CronTrigger(hour=20, minute=0))

    # 매일 밤 10시 비활성 유저 알림
    scheduler.add_job(send_push_to_inactive_users, CronTrigger(hour=22, minute=0))

    scheduler.start()
    _scheduler_started = True  # 이 줄 추가!
    print("스케줄러가 시작되었습니다.")