from rest_framework import serializers
from ..models import Paper, Team, User, TagPaper, Tag

class UserSerializerForPaper(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'mail', 'color', 'team_id')


class PaperSerializer(serializers.ModelSerializer):
    team_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    pk = serializers.SerializerMethodField()
    user = UserSerializerForPaper(read_only=True)
    tags = serializers.SerializerMethodField()
    class Meta:
        model = Paper
        fields = ('pk', 'title', 'team_id', 'user_id', 'created_at', 'user', 'is_open', 'tags', 'is_uploaded')
        read_only_fields = ('created_at', 'pk', )

    def create(self, validated_date):

        validated_date['team'] = validated_date.get('team_id', None)
        validated_date['user'] = validated_date.get('user_id', None)

        if validated_date['team'] is None or validated_date['user'] is None:
            raise serializers.ValidationError("team or user not found.") 

        del validated_date['team_id']
        del validated_date['user_id']

        return Paper.objects.create(**validated_date)
    
    def get_pk(self, obj):
        return int(obj.pk)
    
    def get_tags(self, obj):
        tag_id_list = TagPaper.objects.filter(paper_id=obj.pk).values_list('tag', flat=True)
        tags = Tag.objects.filter(pk__in=tag_id_list).values_list('tag', flat=True)
        return tags