from rest_framework import serializers
from ..models import AnnotationOpen, Annotation, User


class AnnotationOpenSerializer(serializers.ModelSerializer):
    pk = serializers.SerializerMethodField()
    annotation_id = serializers.PrimaryKeyRelatedField(queryset=Annotation.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = AnnotationOpen
        fields = ('pk', 'user_id', 'annotation_id', 'created_at')
        read_only_fields = ('created_at', )

    def create(self, validated_date):

        validated_date['annotation'] = validated_date.get('annotation_id', None)
        validated_date['user'] = validated_date.get('user_id', None)

        if validated_date['annotation'] is None or validated_date['user'] is None:
            raise serializers.ValidationError("user annotation not found.") 

        del validated_date['annotation_id']
        del validated_date['user_id']

        return AnnotationOpen.objects.create(**validated_date)

    def get_pk(self, obj):
        return int(obj.pk)