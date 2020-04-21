from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from .AuthTokenCheck import check_token
from ..models import Tag, TagPaper
from ..serializers.WatchSerializer import WatchSerializer

import uuid

class WatchAPI(generics.CreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = WatchSerializer


    def create(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
