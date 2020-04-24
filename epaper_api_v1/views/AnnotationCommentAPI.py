import os
import base64
import uuid
import datetime
import pytz

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Comment, Watch, AnnotationOpen
from ..serializers.AnnotationCommentSerializer import AnnotationCommentSerializer
from ..serializers.WatchSerializer import WatchSerializer
from ..consts import bucket, bucket_location, AWS_S3_BUCKET_NAME

class AnnotationCommentAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = AnnotationCommentSerializer

    def get_queryset(self, annotation_id):
        return self.queryset.filter(annotation=annotation_id, is_open=True).order_by("created_at")

    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        user_id = request.GET.get("user_id")
        if user_id is None or user_id == "":
            return Response({"status":False, "details":"user_id required."}, status=status.HTTP_400_BAD_REQUEST)

        annotation_id = request.GET.get('annotation_id', None)
        queryset = self.filter_queryset(self.get_queryset(annotation_id))

        serializer = self.get_serializer(queryset, many=True)
        latest_annotation_open = AnnotationOpen.objects.filter(user_id=user_id, annotation_id=annotation_id).order_by("-created_at").first()
        for i, comment in enumerate(serializer.data):
            if comment["user"]["id"] == user_id:
                serializer.data[i]["is_read"] = True
            else:
                if latest_annotation_open is None:
                    serializer.data[i]["is_read"] = False
                else:
                    jst = pytz.timezone("Japan")
                    comment_created_at = datetime.datetime.strptime(comment["created_at"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                    comment_created_at = comment_created_at - datetime.timedelta(hours=9)
                    # comment_created_at = comment_created_at - datetime.timedelta(hours=int(comment["created_at"].split("+")[1].split(":")[0]))
                    serializer.data[i]["is_read"] = comment_created_at.replace(tzinfo=jst) < latest_annotation_open.created_at.replace(tzinfo=jst)
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
        request_data = {
            "user_id": request.data.get("user_id"),
            "annotation_id": request.data.get("annotation_id"),
            "comment": request.data.get("comment", ""),
            "image_url": image_url
        }

        serializer = self.get_serializer(data=request_data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            instance = self.queryset.get(pk=serializer.data["pk"])
            if Watch.objects.filter(user_id=request.data.get("user_id"), paper_id=instance.annotation.paper.id).count() == 0:
                watch_data = {
                    "user_id": request.data.get("user_id"),
                    "paper_id": instance.annotation.paper.id
                }
                watch_serializer = WatchSerializer(data=watch_data)
                watch_serializer.is_valid()
                watch_serializer.save()

            headers = self.get_success_headers(serializer.data)
            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get("user_id")
        comment_id = request.data.get("comment_id")
        new_comment = request.data.get("comment")
        new_image_base64 = request.data.get("image_base64")
        if (new_comment is None or new_comment == "") and (new_image_base64 is None or new_image_base64 == ""):
            return Response({"status":False, "details":"comment or image_base64 required"}, status=status.HTTP_400_BAD_REQUEST)
            
        instance = self.queryset.get(pk=comment_id)
        request_data = {}
        if new_comment != "":
            request_data["comment"] = new_comment
            request_data["image_url"] = ""
        elif new_image_base64 != "":
            url = create_comment_image_url(new_image_base64, "jpg")
            request_data["image_url"] = url
            request_data["comment"] = ""

        if instance.user.id == user_id:
            serializer = self.get_serializer(instance, data=request_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"status":False, "details":"user_id faild"}, status=status.HTTP_400_BAD_REQUEST)
        
def create_comment_image_url(image_base64, extension):
    s3key = 'comments/' + str(uuid.uuid4()) + '.' + extension
    bucket.put_object(Key=s3key, Body=base64.b64decode(image_base64.encode("UTF-8")), ContentType='image/'+extension)

    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], AWS_S3_BUCKET_NAME, s3key)