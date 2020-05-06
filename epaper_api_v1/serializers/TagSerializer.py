from rest_framework import serializers
from ..models import Tag, Team


class TagSerializer(serializers.ModelSerializer):
    pk = serializers.SerializerMethodField()
    team_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    
    class Meta:
        model = Tag
        fields = ('pk', 'tag', 'team_id', 'created_at')
        read_only_fields = ('created_at', )

    def create(self, validated_date):

        validated_date['team'] = validated_date.get('team_id', None)

        if validated_date['team'] is None:
            raise serializers.ValidationError("team not found.") 

        del validated_date['team_id']

        return Tag.objects.create(**validated_date)

    def get_pk(self, obj):
        return int(obj.pk)