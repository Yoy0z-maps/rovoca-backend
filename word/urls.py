from django.urls import path
from .views import WordView, WordbookView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('wordbooks', WordbookView, basename='wordbook')
router.register('words', WordView, basename='word')

urlpatterns = router.urls