from rest_framework import generics, status
from rest_framework.response import Response
from ..models import User, Token, Team
from ..serializers.UserSerializer import UserSerializer
from ..consts import LOGIN_TIME

import datetime
import hashlib

class LoginAPI(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request):
        mail = request.GET.get("mail", None)
        password = request.GET.get("password", None)
        
        user = self.queryset.filter(mail=mail, password=password)
        # userが1人だけに絞れなかったらだめ
        if user.count() != 1:
            return Response({"status":False, "details":"Please enter the correct email address and password."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(user[0])
        login_limit = datetime.datetime.now().timestamp() + LOGIN_TIME

        # token 生成
        str = mail + password + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        hash = hashlib.sha1(str.encode('utf-8')).hexdigest()
        user_token = Token.objects.filter(user_id=serializer.data["id"])
        if user_token.count() != 1:
            Token.objects.create(user_id=serializer.data["id"], token=hash)
        else:
            user_token = Token.objects.get(user_id=serializer.data["id"])
            user_token.token = hash
            user_token.save()

        team_name = Team.objects.get(serializer.data["team_id"]).name
        result_data = {
            "login_limit": int(login_limit),
            "token": hash,
            "id": serializer.data["id"],
            "name": serializer.data["name"],
            "mail": serializer.data["mail"],
            "color": serializer.data["color"],
            "team_id": serializer.data["team_id"],
            "team_name": team_name,
            "is_owner": serializer.data["is_owner"]
        }
        return Response(result_data)