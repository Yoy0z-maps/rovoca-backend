from django.core.management.base import BaseCommand
from users.models import User
from word.models import Wordbook


class Command(BaseCommand):
    help = '기존 사용자들을 위해 기본 워드북을 생성합니다.'

    def handle(self, *args, **options):
        users_without_wordbooks = []
        
        for user in User.objects.all():
            # 사용자가 워드북을 가지고 있지 않으면 기본 워드북 생성
            if not user.wordbooks.exists():
                Wordbook.objects.create(
                    user=user,
                    name="Default",
                    description="Default Voca Bookcase",
                    image="rovoca/default.jpg"
                )
                users_without_wordbooks.append(user.nickname)
        
        if users_without_wordbooks:
            self.stdout.write(
                self.style.SUCCESS(
                    f'다음 사용자들에게 기본 워드북을 생성했습니다: {", ".join(users_without_wordbooks)}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('모든 사용자가 이미 워드북을 가지고 있습니다.')
            ) 