from django.shortcuts import render
from rest_framework import viewsets
from .models import Word, Wordbook
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

# Create your views here.
class WordbookView(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        return Wordbook.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='important')
    def important_wordbook(self):
        try:
            wordbook = self.get_object()
            wordbook.is_important = True
            wordbook.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class WordView(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
       return Word.objects.filter(wordbook__user=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='important')
    def important_word(self):
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
