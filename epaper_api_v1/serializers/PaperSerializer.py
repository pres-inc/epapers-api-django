from rest_framework import serializers
from ..models import Paper, Team, User

class UserSerializerForPaper(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'mail', 'color', 'team_id')


class PaperSerializer(serializers.ModelSerializer):
    team_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    pk = serializers.SerializerMethodField()
    user = UserSerializerForPaper(read_only=True)
    class Meta:
        model = Paper
        fields = ('pk', 'title', 'team_id', 'user_id', 'created_at', 'user', 'is_open')
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