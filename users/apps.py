# users/apps.py

from django.apps import AppConfig
import os
import threading

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # 프로세스당 한 번만 실행되도록 보장
        if not hasattr(self, '_scheduler_started'):
            self._scheduler_started = True
            from .scheduler import start
            start()