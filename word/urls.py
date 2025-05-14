from django.urls import path
from .views import WordView, WordbookView

wordbook_list = WordbookView.as_view({
    'get': 'list',
    'post': 'create'
})
wordbook_detail = WordbookView.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

word_list = WordView.as_view({
    'get': 'list',
    'post': 'create'
})
word_detail = WordView.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('wordbooks/', wordbook_list, name='wordbook-list'),
    path('wordbooks/<int:pk>/', wordbook_detail, name='wordbook-detail'),
    path('words/', word_list, name='word-list'),
    path('words/<int:pk>/', word_detail, name='word-detail'),
]