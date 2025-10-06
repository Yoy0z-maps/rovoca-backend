# user/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as pytz_timezone
import threading

_scheduler_instance = None
_scheduler_lock = threading.Lock()

def start():
    global _scheduler_instance
    with _scheduler_lock:
        if _scheduler_instance is not None and _scheduler_instance.running:
            print("스케줄러가 이미 실행 중입니다.")
            return

        # 동시 실행 1, 누락(coalesce) 통합, 중복 인스턴스 제한
        executors = {"default": ThreadPoolExecutor(1)}  # 잡 동시 실행 최대 1
        job_defaults = {
            "coalesce": True,          # 누락된 실행은 1회로 합쳐서 실행
            "max_instances": 1,        # 같은 잡 중복 인스턴스 금지
            "misfire_grace_time": 300  # 지연 허용 시간(초)
        }

        # 새 스케줄러 생성 (Asia/Seoul)
        _scheduler_instance = BackgroundScheduler(
            timezone=pytz_timezone("Asia/Seoul"),
            executors=executors,
            job_defaults=job_defaults,
        )

        # 잡 등록
        _scheduler_instance.add_job(send_push_with_word, CronTrigger(hour=23, minute=32))
        _scheduler_instance.add_job(send_push_to_all_users, CronTrigger(hour=20, minute=0))
        _scheduler_instance.add_job(send_push_to_inactive_users, CronTrigger(hour=22, minute=0))

        _scheduler_instance.start()
        print("스케줄러가 시작되었습니다.")