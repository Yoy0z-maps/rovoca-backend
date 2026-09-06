from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import Notice


class NoticePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.notice = Notice.objects.create(title="공지", details="내용")

    def test_anyone_can_read_notices(self):
        response = self.client.get("/notice/notices/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["title"], "공지")

    def test_anonymous_user_cannot_create_a_notice(self):
        response = self.client.post(
            "/notice/notices/",
            data={"title": "위조", "details": "차단되어야 함"},
            format="json",
            secure=True,
        )

        self.assertIn(response.status_code, {401, 403})
        self.assertEqual(Notice.objects.count(), 1)

    def test_admin_can_create_a_notice(self):
        admin = get_user_model().objects.create_superuser(
            username="admin",
            social_id="admin-1",
            provider="local",
            nickname="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post(
            "/notice/notices/",
            data={"title": "새 공지", "details": "관리자 작성"},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notice.objects.count(), 2)

    def test_notice_string_is_its_title(self):
        self.assertEqual(str(self.notice), "공지")
