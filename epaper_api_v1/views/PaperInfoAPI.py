import os

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Paper, Watch
from ..serializers.PaperInfoSerializer import PaperInfoSerializer

class PaperInfoAPI(generics.ListAPIView):
    queryset = Paper.objects.all()
    serializer_class = PaperInfoSerializer

    def get_queryset(self, paper_id):
        return self.queryset.get(pk=paper_id)

    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        user_id = request.GET.get("user_id")
        if user_id is None or user_id == "":
            return Response({"status":False, "details":"user_id required."}, status=status.HTTP_400_BAD_REQUEST)
        paper_id = int(request.GET.get('paper_id', None))

        queryset = self.filter_queryset(self.get_queryset(paper_id))

        serializer = self.get_serializer(queryset)

        if checked_result["user"].team_id != serializer.data["team_id"]:
            return Response({"status":False, "details":"You do not have permission to view."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer_data = dict(serializer.data)
        serializer_data["is_watch"] = Watch.objects.filter(user_id=user_id, paper_id=paper_id, is_watch=True).count() > 0
        return Response(serializer_data)
