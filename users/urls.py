from django.urls import path
from .views import SocialLoginView, UserProfileUpdateView
from .views import MeView

urlpatterns = [
    path("auth/social-login/", SocialLoginView.as_view(), name="social-login"),
    path("user/profile/", UserProfileUpdateView.as_view(), name="user-profile-update"),
    path("user/me/", MeView.as_view(), name="user-me"),
]
