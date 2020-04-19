import os

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Annotation
from ..serializers.AnnotationSerializer import AnnotationSerializer
from ..serializers.PaperInfoSerializer import AnnotationSerializerForPaperInfo


class AnnotationAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer

    def get_queryset(self, paper_id):
        # y0 の小さい順の方がいいけどなー
        # get team/paper/info で取得するから一旦パス
        return self.queryset.filter(paper=paper_id, is_open=True).order_by("created_at").reverse()

    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        paper_id = request.GET.get('paper_id', None)
        queryset = self.filter_queryset(self.get_queryset(paper_id))

        serializer = AnnotationSerializerForPaperInfo(queryset, many=True)
        return Response({"annotations":serializer.data})

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
        
    def update(self, request):
        return Response({"status":True, "details": "まだ作ってない"}, status=status.HTTP_202_ACCEPTED)
        
