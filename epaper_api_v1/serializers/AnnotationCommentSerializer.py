from rest_framework import serializers
from ..models import Paper, User, Annotation, Comment

class UserSerializerForComment(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'mail', 'color', 'team_id')


class AnnotationCommentSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    annotation_id = serializers.PrimaryKeyRelatedField(queryset=Annotation.objects.all())
    pk = serializers.SerializerMethodField()
    user = UserSerializerForComment(read_only=True)
    class Meta:
        model = Comment
        fields = ('pk', 'annotation_id', 'comment', 'image_url', 'user_id', 'created_at', 'user')
        read_only_fields = ('created_at', 'pk', )

    def create(self, validated_date):

        validated_date['user'] = validated_date.get('user_id', None)
        validated_date['annotation'] = validated_date.get('annotation_id', None)

        if validated_date['user'] is None or validated_date['annotation'] is None:
            raise serializers.ValidationError("user or annotation not found.") 

        del validated_date['user_id']
        del validated_date['annotation_id']

        return Comment.objects.create(**validated_date)
    
    def get_pk(self, obj):
        return int(obj.pk)