from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import Notice
from .serializers import NoticeSerializer


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all().order_by("-created_at")
    serializer_class = NoticeSerializer

    def get_permissions(self):
        permission_classes = (
            [AllowAny]
            if self.action in {"list", "retrieve"}
            else [IsAdminUser]
        )
        return [permission() for permission in permission_classes]
