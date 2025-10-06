# user/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .tasks import send_push_to_all_users, send_push_to_inactive_users, send_push_with_word
from pytz import timezone

def start():
    scheduler = BackgroundScheduler(timezone=timezone("Asia/Seoul"))

    # 오전 8시 가장 오래된 / 최근 단어 알림
    scheduler.add_job(send_push_with_word, CronTrigger(hour=22, minute=59))

    # 오후 8시 전체 유저 복습 알림
    scheduler.add_job(send_push_to_all_users, CronTrigger(hour=20, minute=-0))

    # 매일 밤 10시 비활성 유저 알림
    scheduler.add_job(send_push_to_inactive_users, CronTrigger(hour=22, minute=0))

    scheduler.start()