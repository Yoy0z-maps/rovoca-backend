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
    
    @action(detail=False, methods=['get'], url_path='id')
    def get_wordbook_by_id(self, request):
        wordbook_id = request.query_params.get('wordbook')
        if not wordbook_id:
            return Response({'error': '워드북 ID를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 워드북 조회수 증가
            wordbook = Wordbook.objects.get(id=wordbook_id, user=self.request.user)
            wordbook.views += 1
            wordbook.save()
            
            # 해당 워드북의 단어들 가져오기
            words = Word.objects.filter(wordbook=wordbook_id)
            word_serializer = WordSerializer(words, many=True)
            wordbook_serializer = WordbookSerializer(wordbook)
            
            return Response({
                'wordbook': wordbook_serializer.data,
                'words': word_serializer.data
            })
        except Wordbook.DoesNotExist:
            return Response({'error': '워드북을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='important')
    def important_wordbook(self, request, pk=None): # Django REST Framework에서 @action으로 커스텀 액션을 만들면, 내부적으로 APIView의 def post(self, request, *args, **kwargs) 같은 구조를 따르기 때문에, DRF가 해당 뷰 메소드를 실행할 때 request를 꼭 넘겨줌.
        try:
            wordbook = self.get_object()
            wordbook.is_important = not wordbook.is_important
            wordbook.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class WordView(viewsets.ModelViewSet):
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()
    
    def get_queryset(self):
        # 유저에 속한 모든 단어
        queryset = Word.objects.filter(wordbook__user=self.request.user)
        
        # wordbook 파라미터가 있으면 해당 워드북의 단어들만 필터링
        wordbook_id = self.request.query_params.get('wordbook')
        if wordbook_id:
            queryset = queryset.filter(wordbook=wordbook_id)
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='important')
    def important_word(self, request, pk=None):
        try:
            word = self.get_object()
            word.is_important = not word.is_important
            word.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='recent')
    def recent_words(self, request):
        # 최근에 추가된 단어 5개를 가져옴
        recent_words = self.get_queryset().order_by('-created_at')[:5]
        serializer = self.get_serializer(recent_words, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='date')
    def words_by_date(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': '날짜를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            words = self.get_queryset().filter(created_at__date=target_date)
            serializer = self.get_serializer(words, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({'error': '올바른 날짜 형식을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='search')
    def search_word(self, request):
        search_text = request.query_params.get('text', '')
        if not search_text:
            return Response({'error': '검색어를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        words = self.get_queryset().filter(text__icontains=search_text)
        serializer = self.get_serializer(words, many=True)
        return Response(serializer.data)
