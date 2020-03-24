from rest_framework import serializers
from ..models import Paper, User, Annotation


class AnnotationSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    paper_id = serializers.PrimaryKeyRelatedField(queryset=Paper.objects.all())
    pk = serializers.SerializerMethodField()
    class Meta:
        model = Annotation
        fields = ('pk', 'paper_id', 'memo', 'coordinate', 'page', 'user_id', 'created_at', 'is_open')
        read_only_fields = ('created_at', 'pk', )

    def create(self, validated_date):

        validated_date['user'] = validated_date.get('user_id', None)
        validated_date['paper'] = validated_date.get('paper_id', None)

        if validated_date['user'] is None or validated_date['paper'] is None:
            raise serializers.ValidationError("user or paper not found.") 

        del validated_date['user_id']
        del validated_date['paper_id']

        return Annotation.objects.create(**validated_date)
    
    def get_pk(self, obj):
        return int(obj.pk)