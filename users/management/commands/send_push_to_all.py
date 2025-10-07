from django.core.management.base import BaseCommand
from users.tasks import send_push_to_all

class Command(BaseCommand):
    help = "매일 모든 유저에게 푸시 전송"

    def handle(self, *args, **kwargs):
        # 여기서 필요한 사전 작업(락 걸기 등)도 가능
        send_push_to_all()
        self.stdout.write(self.style.SUCCESS("Push job done"))