import os
from datetime import datetime
import threading
import shutil

from rest_framework import generics, status
from rest_framework.response import Response
from pdf2image import convert_from_path

from .AuthTokenCheck import check_token
from ..models import Paper, PaperImage, Tag, TagPaper
from ..serializers.PaperSerializer import PaperSerializer
from ..serializers.TagSerializer import TagSerializer
from ..serializers.TagPaperSerializer import TagPaperSerializer
from ..consts import bucket, bucket_location, AWS_S3_BUCKET_NAME



class PaperAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer

    def get_queryset(self, team_id):
        return self.queryset.filter(team=team_id, is_open=True).order_by("created_at").reverse()

    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        team_id = request.GET.get('team_id', None)
        tags = request.GET.get('tags', None)
        if tags is None or tags == "":
            queryset = self.filter_queryset(self.get_queryset(team_id))

            serializer = self.get_serializer(queryset, many=True)
            return Response({"papers":serializer.data})
        else:
            tag_list = list(filter(lambda x: x != "", tags.split(",")))
            tag_id_list = Tag.objects.filter(tag__in=tag_list).values_list('pk', flat=True)
            paper_id_list = list(TagPaper.objects.filter(tag_id__in=tag_id_list).values_list('paper_id', flat=True))
            kind_id = list(set(paper_id_list))
            match_paper_id_list = []
            for ID in kind_id:
                if paper_id_list.count(ID) == len(tag_list):
                    match_paper_id_list.append(ID)

            queryset = self.queryset.filter(team=team_id, is_open=True, pk__in=match_paper_id_list)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({"papers":serializer.data})

    def create(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
            
        tags = request.data.get("tags", "")
        tag_list = list(filter(lambda x: x != "", tags.split(",")))
        create_tags(tag_list)

        user_id = request.data.get("user_id", "tmp")
        team_id = request.data.get("team_id", "0")
        title = request.data.get("title", "no_title")
        file = request.data["file"]

        request_data = {
            "title": title,
            "team_id": team_id,
            "user_id": user_id,
        }

        serializer = self.get_serializer(data=request_data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # pdfを画像化し paperImage に保存
            save_dir_path = "./epaper_api_v1/pdf_files/" + user_id + "/"
            os.makedirs(save_dir_path, exist_ok=True)
            os.makedirs(save_dir_path + "img/", exist_ok=True)
            
            pdf_file_path = os.path.join(save_dir_path, file.name)
            destination = open(pdf_file_path, 'wb')
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()

            paper_id = serializer.data["pk"]
            create_paperImage_and_upload_thread = threading.Thread(target=create_paperImage_and_upload, args=(save_dir_path, pdf_file_path, team_id, paper_id, title))
            create_paperImage_and_upload_thread.start()

            link_tags(tag_list, paper_id)

            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        

    def update(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        title = request.data.get("title")
        if title is None:
            return Response({"status":False, "details":"title is required."}, status=status.HTTP_400_BAD_REQUEST)
        paper_id = request.data.get("paper_id")
        if paper_id is None:
            return Response({"status":False, "details":"paper_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        instance = self.queryset.get(pk=paper_id)
        request_data = {
            "title":title,
            "user_id": instance.user.id,
            "team_id": instance.team_id
        }
        if instance.user.id == request.data.get("user_id"):
            serializer = self.get_serializer(instance, data=request_data)
            if serializer.is_valid(raise_exception=True):
                self.perform_update(serializer)
                return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status":False, "details":"user_id faild"}, status=status.HTTP_400_BAD_REQUEST)

def create_paperImage_and_upload(save_dir_path, pdf_file_path, team_id, paper_id, title):
    
    now = datetime.utcnow()
    images = convert_from_path(pdf_file_path) # pdfを画像化
    for i,image in enumerate(images):
        image_path = save_dir_path + "img/" + str(i) + ".jpg"
        image.save(image_path, quality=95)
        s3key = "paper/" + str(team_id) + "/" + title + "/" + now.strftime('%Y-%m-%d-%H-%M-%S-%f') + "_" + str(i) + ".jpg"
        bucket.upload_file(image_path, s3key)
        url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], AWS_S3_BUCKET_NAME, s3key)
        PaperImage.objects.create(page=i, url=url, paper_id=paper_id)
    # save_dir_path以下のファイルやフォルダを全て削除
    shutil.rmtree(save_dir_path)

def create_tags(tag_list):
    for tag in tag_list:
        if Tag.objects.filter(tag=tag).count() == 0:
            data = {
                "tag":tag
            }
            serializer = TagSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()

def link_tags(tag_list, paper_id):
    for tag in tag_list:
        tag_instance = Tag.objects.filter(tag=tag).first()
        tag_id = tag_instance.pk
        data = {
            "tag_id": tag_id,
            "paper_id": paper_id
        }
        print(data)
        serializer = TagPaperSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()