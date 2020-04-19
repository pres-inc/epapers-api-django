import os

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Comment
from ..serializers.AnnotationCommentSerializer import AnnotationCommentSerializer


class AnnotationCommentDeleteAPI(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = AnnotationCommentSerializer
        
    def get_object(self, annotation_id):
        return self.queryset.get(pk=annotation_id)

    def update(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get("user_id")
        comment_id = request.data.get("comment_id")
        instance = self.get_object(comment_id)
        request_data = {
            "is_open": False
        }
        if instance.user.id == user_id:
            serializer = self.get_serializer(instance, data=request_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"status":False, "details":"user_id faild"}, status=status.HTTP_400_BAD_REQUEST)

        
