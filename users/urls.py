from django.urls import path
from .views import (
    SocialLoginView, UserProfileUpdateView, MeView,
    GameStatusView, GamePlayView, AdRewardView
)

urlpatterns = [
    path("auth/social-login/", SocialLoginView.as_view(), name="social-login"),
    path("user/profile/", UserProfileUpdateView.as_view(), name="user-profile-update"),
    path("user/me/", MeView.as_view(), name="user-me"),

    path("game/status/", GameStatusView.as_view(), name="game-status"),
    path("game/start/", GamePlayView.as_view(), name="game-start"),
    path("game/unlock-by-ad/", AdRewardView.as_view(), name="game-unlock-by-ad"),
]