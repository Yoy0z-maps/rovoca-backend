from django.test import TestCase
from unittest.mock import patch


class HealthEndpointTests(TestCase):
    def test_health_does_not_require_authentication(self):
        response = self.client.get("/health/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_readiness_checks_the_database(self):
        response = self.client.get("/ready/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})


class SocialLoginTests(TestCase):
    @patch("users.views.verify_google_id_token")
    def test_google_login_creates_a_local_session(self, verify_google):
        verify_google.return_value = {
            "id": "google-user-1",
            "email": "user@example.com",
        }

        response = self.client.post(
            "/users/auth/social-login/",
            data={"provider": "google", "result": {"idToken": "token"}},
            content_type="application/json",
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertEqual(response.json()["user"]["provider"], "google")

    @patch("users.views.verify_google_id_token", side_effect=ValueError)
    def test_invalid_google_login_is_rejected(self, _verify_google):
        response = self.client.post(
            "/users/auth/social-login/",
            data={"provider": "google", "result": {"idToken": "invalid"}},
            content_type="application/json",
            secure=True,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(), {"error": "Invalid social login credential"}
        )
