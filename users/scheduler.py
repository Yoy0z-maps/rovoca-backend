# user/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .tasks import send_push_to_all_users, send_push_to_inactive_users

def start():
    scheduler = BackgroundScheduler()

    # 매일 오전 8시, 오후 8시 전체 유저 알림
    scheduler.add_job(send_push_to_all_users, CronTrigger(hour=8, minute=0))
    scheduler.add_job(send_push_to_all_users, CronTrigger(hour=22, minute=43))

    # 매일 밤 11시 비활성 유저 알림
    scheduler.add_job(send_push_to_inactive_users, CronTrigger(hour=18, minute=0))

    scheduler.start()