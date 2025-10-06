# user/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .tasks import send_push_to_all_users, send_push_to_inactive_users, send_push_with_word
from pytz import timezone
import threading
import os

# 전역 스케줄러 인스턴스와 락
_scheduler_instance = None
_scheduler_lock = threading.Lock()

def start():
    global _scheduler_instance
    
    with _scheduler_lock:
        # 이미 스케줄러가 실행 중인지 확인
        if _scheduler_instance is not None and _scheduler_instance.running:
            print("스케줄러가 이미 실행 중입니다.")
            return
        
        # 기존 스케줄러가 있다면 종료
        if _scheduler_instance is not None:
            try:
                _scheduler_instance.shutdown()
            except:
                pass
        
        # 새 스케줄러 생성
        _scheduler_instance = BackgroundScheduler(timezone=timezone("Asia/Seoul"))

        # 오전 8시 가장 오래된 / 최근 단어 알림
        _scheduler_instance.add_job(send_push_with_word, CronTrigger(hour=23, minute=12))

        # 오후 8시 전체 유저 복습 알림
        _scheduler_instance.add_job(send_push_to_all_users, CronTrigger(hour=20, minute=0))

        # 매일 밤 10시 비활성 유저 알림
        _scheduler_instance.add_job(send_push_to_inactive_users, CronTrigger(hour=22, minute=0))

        _scheduler_instance.start()
        print("스케줄러가 시작되었습니다.")

def stop():
    global _scheduler_instance
    
    with _scheduler_lock:
        if _scheduler_instance is not None:
            _scheduler_instance.shutdown()
            _scheduler_instance = None
            print("스케줄러가 종료되었습니다.")