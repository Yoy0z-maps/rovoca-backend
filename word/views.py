from django.shortcuts import render
from rest_framework import viewsets
from .models import Word, Wordbook
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .serializers import WordbookSerializer, WordSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class WordbookView(viewsets.ModelViewSet):
    serializer_class = WordbookSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        return Wordbook.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1  # 조회수 증가
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='important')
    def important_wordbook(self, request, pk=None): # Django REST Framework에서 @action으로 커스텀 액션을 만들면, 내부적으로 APIView의 def post(self, request, *args, **kwargs) 같은 구조를 따르기 때문에, DRF가 해당 뷰 메소드를 실행할 때 request를 꼭 넘겨줌.
        try:
            wordbook = self.get_object()
            wordbook.is_important = True
            wordbook.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class WordView(viewsets.ModelViewSet):
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
       return Word.objects.filter(wordbook__user=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='important')
    def important_word(self, request, pk=None):
        try:
            word = self.get_object()
            word.is_important = True
            word.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='search')
    def search_word(self, request):
        search_text = request.query_params.get('text', '')
        if not search_text:
            return Response({'error': '검색어를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        words = self.get_queryset().filter(text__icontains=search_text)
        serializer = self.get_serializer(words, many=True)
        return Response(serializer.data)
