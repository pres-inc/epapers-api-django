import os
from datetime import datetime
import threading
import shutil

from rest_framework import generics, status
from rest_framework.response import Response
from pdf2image import convert_from_path

from ..models import Paper, PaperImage
from ..serializers.PaperSerializer import PaperSerializer
from ..consts import bucket, AWS_S3_BUCKET_NAME



class PaperAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer

    def list(self, request):

        return Response({"papers":""})

    def create(self, request):
        user_id = request.data.get("user_id", "tmp")
        team_id = request.data.get("team_id", 0)
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

            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
        

        

    def update(self, request):
        return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        

def create_paperImage_and_upload(save_dir_path, pdf_file_path, team_id, paper_id, title):
    
    now = datetime.utcnow()
    images = convert_from_path(pdf_file_path) # pdfを画像化
    for i,image in enumerate(images):
        image_path = save_dir_path + "img/" + str(i) + ".jpg"
        image.save(image_path, quality=95)
        s3key = "paper/" + str(team_id) + "/" + title + "/" + now.strftime('%Y-%m-%d-%H-%M-%S-%f') + "_" + str(i) + ".jpg"
        bucket.upload_file(image_path, s3key)
        url = 'https://s3-ap-northeast-1.amazonaws.com/{}/{}'.format(AWS_S3_BUCKET_NAME, s3key)
        PaperImage.objects.create(page=i, url=url, paper_id=paper_id)
    # save_dir_path以下のファイルやフォルダを全て削除
    shutil.rmtree(save_dir_path)