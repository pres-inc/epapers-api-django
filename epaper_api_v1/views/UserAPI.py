from rest_framework import generics, status
from rest_framework.response import Response
from ..models import User, Team
from ..serializers.UserSerializer import UserSerializer
from .AuthTokenCheck import check_token

import uuid

class UserAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self, user_id, team_id):
        if user_id is not None:
            return self.queryset.filter(id=user_id)
        elif team_id is not None:
            return self.queryset.filter(team=team_id)
        return None

    def list(self, request):
        checked_result = check_token(request.GET.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.GET.get('user_id', None)
        team_id = request.GET.get('team_id', None)
        queryset = self.filter_queryset(self.get_queryset(user_id, team_id))

        serializer = self.get_serializer(queryset, many=True)
        return Response({"users":serializer.data})

    def create(self, request):
        # 確認用パスワードが間違ってたらだめ
        password = request.data.get("password")
        password_conf = request.data.get("password_conf")
        if password != password_conf:
            return Response({"status":False, "details":"password != password_conf"}, status=status.HTTP_400_BAD_REQUEST)
        

        # メールアドレスがすでに使用されていたらだめ
        mail = request.data.get("mail", None)
        if mail is not None and self.queryset.filter(mail=mail).count() > 0:
            return Response({"status":False, "details":"mail address already used"}, status=status.HTTP_400_BAD_REQUEST)
        
        # オーナーでチーム名を設定している場合, チーム名変更
        is_owner = request.data.get("is_owner", False)
        team_id = request.data.get("team_id")
        new_id = str(uuid.uuid4())
        request.data.update(id=new_id)
        serializer = self.get_serializer(data=request.data)
        if is_owner:
            if self.queryset.filter(team_id=team_id, is_owner=True).count != 0:
                return Response({"status":False, "details":"Owner already exists."}, status=status.HTTP_400_BAD_REQUEST)
            team_name = request.data.get("team_name", None)
            if team_name is not None:
                # team 名前変更
                team_obj = Team.objects.get(id=team_id)
                team_obj.name = team_name
                team_obj.save()
        
        
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({"status":True}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request):
        checked_result = check_token(request.data.get('Auth', None))
        if not checked_result["status"]:
            return Response({"status":False, "details":"Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        # 確認用パスワードが間違ってたらだめ
        password = request.data.get("password", None)
        password_conf = request.data.get("password_conf", None)
        if password != password_conf:
            return Response({"status":False, "details":"password != password_conf"}, status=status.HTTP_400_BAD_REQUEST)
        
        # メールアドレスがすでに使用されていたらだめ
        mail = request.data.get("mail", None)
        if mail is not None and self.queryset.filter(mail=mail).count() > 0:
            return Response({"status":False, "details":"mail address already used"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = request.data.get("id")
        instance = self.queryset.get(id=user_id)
        team_id = instance.team_id
        is_owner = instance.is_owner
        # オーナーでチーム名を設定している場合, チーム名変更
        if is_owner:
            team_name = request.data.get("team_name", None)
            if team_name is not None:
                # team 名前変更
                team_obj = Team.objects.get(id=team_id)
                team_obj.name = team_name
                team_obj.save()
        request.data.update(mail=request.data.get("mail", instance.mail))
        request.data.update(password=request.data.get("password", instance.password))
        request.data.update(team_id=team_id)
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_update(serializer)
            return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)
