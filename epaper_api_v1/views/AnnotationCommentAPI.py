import os
import base64
import uuid

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Comment
from ..serializers.AnnotationCommentSerializer import AnnotationCommentSerializer
from ..consts import bucket, bucket_location, AWS_S3_BUCKET_NAME

class AnnotationCommentAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = AnnotationCommentSerializer

    def get_queryset(self, annotation_id):
        # y0 の小さい順の方がいいけどなー
        # get team/paper/info で取得するから一旦パス
        return self.queryset.filter(annotation=annotation_id).order_by("created_at")

    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        annotation_id = request.GET.get('annotation_id', None)
        queryset = self.filter_queryset(self.get_queryset(annotation_id))

        serializer = self.get_serializer(queryset, many=True)
        return Response({"comments":serializer.data})

    def create(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
            
        comment = request.data.get("comment", None)
        image_base64 = request.data.get("image_base64", None)
        if (comment is None or comment == "") and (image_base64 is None or image_base64 == ""):
            return Response({"status":False, "details": "comment or image_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        image_url = ""
        if image_base64 is not None and image_base64 != "":
            image_url = create_comment_image_url(image_base64, "jpg")
        # request.data.update(image_url=image_url)
        request_data = {
            "user_id": request.data.get("user_id"),
            "annotation_id": request.data.get("annotation_id"),
            "comment": request.data.data.get("comment", ""),
            "image_url": image_url
        }

        serializer = self.get_serializer(data=request_data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request):
        return Response({"status":True, "details": "まだ作ってない"}, status=status.HTTP_202_ACCEPTED)
        
def create_comment_image_url(image_base64, extension):
    s3key = 'comments/' + str(uuid.uuid4()) + '.' + extension
    bucket.put_object(Key=s3key, Body=base64.b64decode(image_base64.encode("UTF-8")), ContentType='image/'+extension)

    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], AWS_S3_BUCKET_NAME, s3key)