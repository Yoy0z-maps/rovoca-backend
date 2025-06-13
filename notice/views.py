from rest_framework import viewsets
from .models import Notice
from .serializers import NoticeSerializer
from rest_framework.permissions import AllowAny

class NoticeViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    queryset = Notice.objects.all().order_by('-created_at')
    serializer_class = NoticeSerializer