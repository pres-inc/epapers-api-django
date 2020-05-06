from rest_framework import generics, status
from rest_framework.response import Response
from ..models import User, Team
from ..serializers.TeamSerializer import TeamSerializer
from .AuthTokenCheck import check_token
import uuid

class TeamAPI(generics.UpdateAPIView, generics.ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


    def list(self, request):
        team_id = request.GET.get("team_id")
        queryset = self.queryset.get(id=team_id)

        serializer = self.get_serializer(queryset)
        return Response({"team":serializer.data})

    def create(self, request):

        if request.data.get("id", None) is None:
            new_id = str(uuid.uuid4())
            request.data.update(id=new_id)

        serializer = self.get_serializer(data=request.data)
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
        
        user_id = request.data.get("user_id")
        request_user = User.objects.get(id=user_id)
        if not request_user.is_owner:
            return Response({"status":False, "details":"not owner."}, status=status.HTTP_400_BAD_REQUEST)
        team_id = request.data.get("team_id")
        instance = self.queryset.get(id=team_id)
        request_data = {
            "name": request.data.get("team_name")
        }
        serializer = self.get_serializer(instance, data=request_data, partial=True)
        if serializer.is_valid(raise_exception=True):
            self.perform_update(serializer)
            return Response({"status":True}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"status":False}, status=status.HTTP_400_BAD_REQUEST)