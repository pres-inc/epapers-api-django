from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from .AuthTokenCheck import check_token
from ..models import Tag, TagPaper
from ..serializers.TagSerializer import TagSerializer

import uuid

class TagAPI(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        
        tag_name = request.GET.get("tag_name")
        tag_filter = Q()
        if tag_name is not None and tag_name != "":
            tag_filter = Q(tag__tag__contains=tag_name)

        team_id = request.GET.get("team_id")
        tag_id_list = list(set(TagPaper.objects.filter(Q(paper__team__pk=team_id) & tag_filter).values_list('tag', flat=True)))
        queryset = self.queryset.filter(pk__in=tag_id_list)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"tags":serializer.data})
