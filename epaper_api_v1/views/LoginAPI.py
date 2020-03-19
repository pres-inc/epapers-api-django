from rest_framework import generics, status
from rest_framework.response import Response
from ..models import User
from ..serializers.UserSerializer import UserSerializer

import datetime

login_time = 60 * 60 * 24

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
        login_limit = datetime.datetime.now().timestamp() + login_time
        
        result_data = {
            "login_limit": int(login_limit),
            "id": serializer.data["id"],
            "name": serializer.data["name"],
            "mail": serializer.data["mail"],
            "color": serializer.data["color"],
            "team_id": serializer.data["team_id"],
            "is_owner": serializer.data["is_owner"]
        }
        return Response(result_data)