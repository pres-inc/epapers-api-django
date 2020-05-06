from rest_framework import serializers
from ..models import TagPaper, Paper, Tag
from .PaperSerializer import PaperSerializer
from .TagSerializer import TagSerializer


class TagPaperSerializer(serializers.ModelSerializer):
    paper_id = serializers.PrimaryKeyRelatedField(queryset=Paper.objects.all())
    tag_id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    pk = serializers.SerializerMethodField()
    paper = PaperSerializer(read_only=True)
    tag = TagSerializer(read_only=True)
    class Meta:
        model = TagPaper
        fields = ('pk', 'tag', 'tag_id', 'paper', 'paper_id')
    
    def create(self, validated_date):

        validated_date['tag'] = validated_date.get('tag_id', None)
        validated_date['paper'] = validated_date.get('paper_id', None)

        if validated_date['tag'] is None or validated_date['paper'] is None:
            raise serializers.ValidationError("tag or paper not found.") 

        del validated_date['tag_id']
        del validated_date['paper_id']

        return TagPaper.objects.create(**validated_date)

    def get_pk(self, obj):
        return int(obj.pk)