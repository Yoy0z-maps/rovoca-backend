# users/apps.py

from django.apps import AppConfig
import os

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # 개발 환경에서 중복 실행 방지
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        from .scheduler import start
        start()