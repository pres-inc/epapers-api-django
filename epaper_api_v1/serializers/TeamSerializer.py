from rest_framework import serializers
from ..models import Team


class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = ('name', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    