from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

class Command(BaseCommand):
    help = "Deletes refresh tokens older than 30 days."

    def handle(self, *args, **kwargs):
        cutoff = now() - timedelta(days=30)

        blacklisted_deleted, _ = BlacklistedToken.objects.filter(token__created_at__lt=cutoff).delete()

        outstanding_deleted, _ = OutstandingToken.objects.filter(created_at__lt=cutoff).delete()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Deleted {blacklisted_deleted} blacklisted tokens and {outstanding_deleted} outstanding tokens older than 30 days."
        ))