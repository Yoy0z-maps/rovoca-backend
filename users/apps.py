from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from .scheduler import start
        start()
