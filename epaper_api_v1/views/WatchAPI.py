from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from .AuthTokenCheck import check_token
from ..models import Watch
from ..serializers.WatchSerializer import WatchSerializer

import uuid

class WatchAPI(generics.CreateAPIView):
    queryset = Watch.objects.all()
    serializer_class = WatchSerializer


    def create(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        user_id = request.data.get("user_id")
        paper_id = request.data.get("paper_id")
        instance = self.queryset.get(user_id=user_id, paper_id=paper_id)
        if instance is None:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)

        else:
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({"status":True}, status=status.HTTP_201_CREATED)
            else:
                return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
