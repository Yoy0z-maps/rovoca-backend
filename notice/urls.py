from django.urls import path
from .views import NoticeViewSet

notice_list = NoticeViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

notice_detail = NoticeViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('notices/', notice_list, name='notice-list'),
    path('notices/<int:pk>/', notice_detail, name='notice-detail'),
]

'''
Notice 목록 관련:
GET /notices/ - 모든 Notice 조회
POST /notices/ - 새로운 Notice 생성
개별 Notice 관련:
GET /notices/<int:pk>/ - 특정 Notice 조회
PUT /notices/<int:pk>/ - 특정 Notice 전체 수정
PATCH /notices/<int:pk>/ - 특정 Notice 부분 수정
DELETE /notices/<int:pk>/ - 특정 Notice 삭제
'''