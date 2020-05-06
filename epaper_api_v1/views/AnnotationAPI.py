import os
import base64
import uuid

from rest_framework import generics, status
from rest_framework.response import Response

from .AuthTokenCheck import check_token
from ..models import Annotation, Watch
from ..serializers.AnnotationSerializer import AnnotationSerializer
from ..serializers.PaperInfoSerializer import AnnotationSerializerForPaperInfo
from ..serializers.WatchSerializer import WatchSerializer
from ..consts import bucket, bucket_location, AWS_S3_BUCKET_NAME


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
        
        memo = request.data.get("memo", None)
        image_base64 = request.data.get("image_base64", None)
        if (memo is None or memo == "") and (image_base64 is None or image_base64 == ""):
            return Response({"status":False, "details": "memo or image_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        image_url = ""
        if image_base64 is not None and image_base64 != "":
            image_url = create_comment_image_url(image_base64, "jpg")
        
        request_data = {
            "user_id": request.data.get("user_id"),
            "page": request.data.get("page"),
            "paper_id": request.data.get("paper_id"),
            "coordinate": request.data.get("coordinate"),
            "memo": request.data.get("memo", ""),
            "image_url": image_url
        }

        serializer = self.get_serializer(data=request_data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            if Watch.objects.filter(user_id=request.data.get("user_id"), paper_id=request.data.get("paper_id")).count() == 0:
                watch_data = {
                    "user_id": request.data.get("user_id"),
                    "paper_id": request.data.get("paper_id")
                }
                watch_serializer = WatchSerializer(data=watch_data)
                watch_serializer.is_valid()
                watch_serializer.save()

            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get("user_id")
        annotation_id = request.data.get("annotation_id")
        instance = self.queryset.get(pk=annotation_id)
        request_data = {
            "user_id": instance.user.id,
        }

        memo = request.data.get("memo", None)
        image_base64 = request.data.get("image_base64", None)
        if (memo is None or memo == "") and (image_base64 is None or image_base64 == ""):
            return Response({"status":False, "details": "memo or image_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        image_url = ""
        if image_base64 is not None and image_base64 != "":
            image_url = create_comment_image_url(image_base64, "jpg")
        
        request_data["image_url"] = image_url
        request_data["memo"] = request.data.get("memo", "")

        coordinate = request.data.get("coordinate")
        if  coordinate is not None and coordinate != "":
            request_data["coordinate"] = coordinate

        page = request.data.get("page")
        if  page is not None and page != "":
            request_data["page"] = page

        if instance.user.id == user_id:
            serializer = self.get_serializer(instance, data=request_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"status":False, "details":"user_id faild"}, status=status.HTTP_400_BAD_REQUEST)
        
def create_comment_image_url(image_base64, extension):
    s3key = 'memo/' + str(uuid.uuid4()) + '.' + extension
    bucket.put_object(Key=s3key, Body=base64.b64decode(image_base64.encode("UTF-8")), ContentType='image/'+extension)

    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], AWS_S3_BUCKET_NAME, s3key)