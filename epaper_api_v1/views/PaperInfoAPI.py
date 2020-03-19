import os

from rest_framework import generics, status
from rest_framework.response import Response

from ..models import Paper
from ..serializers.PaperInfoSerializer import PaperInfoSerializer

class PaperInfoAPI(generics.ListAPIView):
    queryset = Paper.objects.all()
    serializer_class = PaperInfoSerializer

    def get_queryset(self, paper_id):
        return self.queryset.get(pk=paper_id)

    def list(self, request):
        paper_id = request.GET.get('paper_id', None)
        queryset = self.filter_queryset(self.get_queryset(paper_id))

        serializer = self.get_serializer(queryset)

        return Response(serializer.data)
