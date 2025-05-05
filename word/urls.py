
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WordbookView, WordView

router = DefaultRouter()
router.register(r'wordbooks', WordbookView, basename='wordbook')
router.register(r'words', WordView, basename='word')

urlpatterns = [
    path('', include(router.urls)),
]