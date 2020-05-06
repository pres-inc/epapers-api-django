import os
from datetime import datetime
import pytz

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Paper, Watch, AnnotationOpen, Comment, PaperOpen, Annotation
from ..serializers.PaperInfoSerializer import PaperInfoSerializer
from ..serializers.PaperOpenSerializer import PaperOpenSerializer

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
        paper_annotation_open = AnnotationOpen.objects.filter(user_id=user_id, annotation__paper_id=paper_id)
        paper_comment = Comment.objects.filter(annotation__paper_id=paper_id, is_open=True)
        latest_paper_open = PaperOpen.objects.filter(paper_id=paper_id, user_id=user_id).order_by("-created_at").first()
        paper_open_serializer = PaperOpenSerializer(latest_paper_open)
        for i, annotation in enumerate(serializer_data["annotations"]):
            if serializer_data["is_watch"]:
                latest_annotation_open = paper_annotation_open.filter(annotation_id=annotation["pk"]).order_by("-created_at").first()
                if latest_annotation_open is None:
                    serializer_data["annotations"][i]["unread_count"] = paper_comment.exclude(user_id=user_id).filter(annotation_id=annotation["pk"]).count()
                else:
                    serializer_data["annotations"][i]["unread_count"] = paper_comment.exclude(user_id=user_id).filter(created_at__gte=latest_annotation_open.created_at, annotation_id=annotation["pk"]).count()
            else:
                serializer_data["annotations"][i]["unread_count"] = 0

            # print(annotation["created_at"])
            if annotation["user"]["id"] == user_id:
                serializer_data["annotations"][i]["is_read"] = True
            else:
                if latest_paper_open is not None:
                    print(paper_open_serializer.data)
                    latest_paper_open_created_at = datetime.strptime(paper_open_serializer.data["created_at"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                    annotation_created_at = datetime.strptime(annotation["created_at"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                    
                    # print(latest_paper_open.created_at)
                    serializer_data["annotations"][i]["is_read"] = annotation_created_at < latest_paper_open_created_at
                else:
                    serializer_data["annotations"][i]["is_read"] = False
        return Response(serializer_data)
