from rest_framework import serializers
from ..models import User, Team


class UserSerializer(serializers.ModelSerializer):
    team_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    class Meta:
        model = User
        fields = ('id', 'name', 'mail', 'password', 'color', 'team_id', 'is_owner', 'created_at')
        read_only_fields = ('created_at',)

    def create(self, validated_date):

        validated_date['team'] = validated_date.get('team_id', None)

        if validated_date['team'] is None:
            raise serializers.ValidationError("team not found.") 

        del validated_date['team_id']

        return User.objects.create(**validated_date)
    