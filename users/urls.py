from django.urls import path
from .views import (
    SocialLoginView, UserProfileUpdateView, MeView,
    GameStatusView, GamePlayView, AdRewardView, UserDeleteView, ScoreUpdateView
)

urlpatterns = [
    path("auth/social-login/", SocialLoginView.as_view(), name="social-login"),
    path("user/profile/", UserProfileUpdateView.as_view(), name="user-profile-update"),
    path("user/me/", MeView.as_view(), name="user-me"),
    path("user/delete/", UserDeleteView.as_view(), name="user-delete"),

    path("user/score/", ScoreUpdateView.as_view(), name="user-score-update"),

    path("game/status/", GameStatusView.as_view(), name="game-status"),
    path("game/start/", GamePlayView.as_view(), name="game-start"),
    path("game/unlock-by-ad/", AdRewardView.as_view(), name="game-unlock-by-ad"),
]