from rest_framework import serializers
from .models import Word, Wordbook

class WordbookSerializer(serializers.ModelSerializer):
    word_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Wordbook
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user', 'word_count']

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = '__all__'
        read_only_fields = ['id', 'created_at']