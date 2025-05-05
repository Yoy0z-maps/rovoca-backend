from rest_framework import serializers
from .models import Word, Wordbook

class WordbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wordbook
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        return Wordbook.objects.create(user=user, **validated_data)

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = '__all__'
        read_only_fields = ['id', 'created_at']