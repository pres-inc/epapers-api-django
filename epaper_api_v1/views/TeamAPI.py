from rest_framework import generics, status
from rest_framework.response import Response
from ..models import User, Team
from ..serializers.TeamSerializer import TeamSerializer

import uuid

class TeamAPI(generics.ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response({"teams":serializer.data})

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
