import os
from datetime import datetime
import threading
import shutil

from rest_framework import generics, status
from rest_framework.response import Response
from pdf2image import convert_from_path

from .AuthTokenCheck import check_token
from ..models import Paper, PaperImage, Tag, TagPaper, Comment, Annotation, User, Watch, PaperOpen, AnnotationOpen
from ..serializers.PaperSerializer import PaperSerializer
from ..serializers.TagSerializer import TagSerializer
from ..serializers.TagPaperSerializer import TagPaperSerializer
from ..serializers.UserSerializer import UserSerializer
from ..serializers.WatchSerializer import WatchSerializer
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
        user_id = request.GET.get("user_id")
        if user_id is None or user_id == "":
            return Response({"status":False, "details":"user_id required."}, status=status.HTTP_400_BAD_REQUEST)
        team_id = request.GET.get('team_id', None)
        tags = request.GET.get('tags', None)
        if tags is None or tags == "":
            queryset = self.filter_queryset(self.get_queryset(team_id))
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
        
        all_tag_paper = TagPaper.objects.filter(paper__team_id=team_id)
        all_annotation = Annotation.objects.filter(paper__team_id=team_id, is_open=True)
        all_comment = Comment.objects.filter(annotation_id__in=all_annotation, is_open=True)
        all_user = User.objects.filter(team_id=team_id)
        all_paper_open = PaperOpen.objects.filter(paper__team_id=team_id, user_id=user_id)
        all_annotation_open = AnnotationOpen.objects.filter(annotation_id__in=all_annotation, user_id=user_id)

        user_watch_list = Watch.objects.filter(user_id=user_id, is_watch=True).values_list("paper_id", flat=True)
        
        my_papers = []
        other_papers = []
        serializer = self.get_serializer(queryset, many=True)
        for i, paper in enumerate(serializer.data):
            paper_annotation = all_annotation.filter(paper_id=paper["pk"])
            paper_comment = all_comment.filter(annotation_id__in=paper_annotation)
            action_user_id_list = list(paper_annotation.values_list("user_id", flat=True))
            action_user_id_list.extend(list(paper_comment.values_list("user_id", flat=True)))
            action_user = all_user.filter(id__in=action_user_id_list)
            user_serializer = UserSerializer(action_user, many=True)
            serializer.data[i]["action_users"] = user_serializer.data
            serializer.data[i]["tags"] = all_tag_paper.filter(paper_id=paper["pk"]).values_list('tag__tag', flat=True)
            
            # 最新アクション時間を記録
            latest_my_annotation = paper_annotation.filter(user_id=user_id).order_by("created_at").first()
            latest_my_comment = paper_comment.filter(user_id=user_id).order_by("created_at").first()
            
            if latest_my_annotation is None and latest_my_comment is None:
                latest_actioned_at = None
            elif latest_my_annotation is not None and latest_my_comment is None:
                latest_actioned_at = latest_my_annotation.created_at
            elif latest_my_annotation is None and latest_my_comment is not None:
                latest_actioned_at = latest_my_comment.created_at
            elif latest_my_annotation is not None and latest_my_comment is not None:
                latest_actioned_at = latest_my_comment.created_at if latest_my_comment.created_at > latest_my_annotation.created_at else latest_my_annotation.created_at
            
            serializer.data[i]["latest_actioned_at"] = latest_actioned_at

            if paper["pk"] in user_watch_list:
                latest_paper_open = all_paper_open.filter(paper_id=paper["pk"], user_id=user_id).order_by("-created_at").first()
                new_annotation_count = 0
                if latest_paper_open is not None:
                    new_annotation_count = all_annotation.exclude(user_id=user_id).filter(paper_id=paper["pk"], created_at__gte=latest_paper_open.created_at, is_open=True).count()
                
                new_comment_count = get_new_comment_count(all_annotation, all_comment, all_annotation_open, paper["pk"], user_id)
                # 通知数計算をやる
                serializer.data[i]["new_annotation_count"] = new_annotation_count
                serializer.data[i]["new_comment_count"] = new_comment_count
                my_papers.append(serializer.data[i])
            else:
                serializer.data[i]["new_annotation_count"] = 0
                serializer.data[i]["new_comment_count"] = 0
                other_papers.append(serializer.data[i])
            
        my_papers = sorted(my_papers, key=lambda x:(x['latest_actioned_at'] is not None, x['latest_actioned_at']), reverse=True)
        other_papers = sorted(other_papers, key=lambda x:(x['latest_actioned_at'] is not None, x['latest_actioned_at']), reverse=True)
        return Response({"papers":other_papers, "my_papers":my_papers})

    def create(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        
        team_id = request.data.get("team_id", "0")
        tags = request.data.get("tags", "")
        tag_list = list(filter(lambda x: x != "", tags.split(",")))
        create_tags(tag_list, team_id)

        user_id = request.data.get("user_id", "tmp")
        title = request.data.get("title", "no_title")
        file = request.data["file"]

        request_data = {
            "title": title,
            "team_id": team_id,
            "user_id": user_id,
            "is_uploaded": False
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
            
            # 論文アップロード者はwatchする
            watch_data = {
                "user_id":user_id,
                "paper_id":serializer.data["pk"]
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

        title = request.data.get("title")
        
        paper_id = request.data.get("paper_id")
        if paper_id is None:
            return Response({"status":False, "details":"paper_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        instance = self.queryset.get(pk=paper_id)
        if instance.user.id != request.data.get("user_id"):
            return Response({"status":False, "details":"user_id faild"}, status=status.HTTP_400_BAD_REQUEST)

        tags = request.data.get("tags")
        if tags is not None and tags != "":
            tag_list = list(filter(lambda x: x != "", tags.split(",")))
            create_tags(tag_list, instance.team_id)
            update_TagPaper(tag_list, paper_id)

        request_data = {}
        if title is not None and title != "":
            request_data["title"] = title

        
        serializer = self.get_serializer(instance, data=request_data, partial=True)
        if serializer.is_valid(raise_exception=True):
            self.perform_update(serializer)
            return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        

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

    # 論文画像のアップロード完了パラメータをtrueにする
    paper_instance = Paper.objects.get(pk=paper_id)
    paper_serializer = PaperSerializer(paper_instance, data={"is_uploaded":True}, partial=True)
    paper_serializer.is_valid()
    paper_serializer.save()

def create_tags(tag_list, team_id):
    for tag in tag_list:
        if Tag.objects.filter(tag=tag, team_id=team_id).count() == 0:
            data = {
                "tag":tag,
                "team_id": team_id
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
        serializer = TagPaperSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

def update_TagPaper(tag_list, paper_id):
    tag_paper_list = TagPaper.objects.filter(paper_id=paper_id)
    tag_id_list = Tag.objects.filter(tag__in=tag_list).values_list('pk', flat=True)
    # 新たな設定タグに含まれていない既存タグは消す
    # すでに設定されているタグがあれば tag_list から消す
    for tag_paper in tag_paper_list:
        if tag_paper.tag.pk not in tag_id_list:
            tag_paper.delete()
        else:
            tag_list.remove(tag_paper.tag.tag)

    link_tags(tag_list, paper_id)

def get_new_comment_count(all_annotation, all_comment, all_annotation_open, paper_id, user_id):
    paper_annotation = all_annotation.filter(paper_id=paper_id)
    new_comment_count = 0
    for annotation in paper_annotation:
        latest_annotation_open = all_annotation_open.filter(annotation_id=annotation.pk).order_by("-created_at").first()
        if latest_annotation_open is None:
            new_comment_count += all_comment.exclude(user_id=user_id).filter(annotation_id=annotation.pk).count()
        else:
            new_comment_count += all_comment.exclude(user_id=user_id).filter(annotation_id=annotation.pk, created_at__gte=latest_annotation_open.created_at).count()
    return new_comment_count