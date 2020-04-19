from rest_framework import serializers
from ..models import Tag


class TagSerializer(serializers.ModelSerializer):
    pk = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ('pk', 'tag', 'created_at')
        read_only_fields = ('created_at', )

    def get_pk(self, obj):
        return int(obj.pk)