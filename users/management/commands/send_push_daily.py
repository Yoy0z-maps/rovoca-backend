# yourapp/management/commands/sendpush_daily.py
from django.core.management.base import BaseCommand
from yourapp.push import send_push_with_word  # 네가 쓰는 함수 import

class Command(BaseCommand):
    help = "매일 단어 푸시 전송"

    def handle(self, *args, **kwargs):
        # 여기서 필요한 사전 작업(락 걸기 등)도 가능
        send_push_with_word()
        self.stdout.write(self.style.SUCCESS("Push job done"))