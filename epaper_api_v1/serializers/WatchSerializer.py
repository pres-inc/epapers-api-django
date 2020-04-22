from rest_framework import serializers
from ..models import Watch, Paper, User


class WatchSerializer(serializers.ModelSerializer):
    pk = serializers.SerializerMethodField()
    paper_id = serializers.PrimaryKeyRelatedField(queryset=Paper.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Watch
        fields = ('pk', 'user_id', 'paper_id', 'is_watch','created_at')
        read_only_fields = ('created_at', )

    def create(self, validated_date):

        validated_date['paper'] = validated_date.get('paper_id', None)
        validated_date['user'] = validated_date.get('user_id', None)

        if validated_date['paper'] is None or validated_date['user'] is None:
            raise serializers.ValidationError("user paper not found.") 

        del validated_date['paper_id']
        del validated_date['user_id']

        return Watch.objects.create(**validated_date)

    def get_pk(self, obj):
        return int(obj.pk)