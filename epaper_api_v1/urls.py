from django.urls import path
from rest_framework import routers
from rest_framework import urlpatterns as urlp

from .views.UserAPI import UserAPI
from .views.LoginAPI import LoginAPI
from .views.PaperAPI import PaperAPI
from .views.AnnotationAPI import AnnotationAPI
from .views.AnnotationCommentAPI import AnnotationCommentAPI
from .views.PaperInfoAPI import PaperInfoAPI
from .views.TeamAPI import TeamAPI
from .views.AnnotationDeleteAPI import AnnotationDeleteAPI

router = routers.DefaultRouter()
urlpatterns = {
    path('team/user/', UserAPI.as_view()),
    path('team/login/', LoginAPI.as_view()),
    path('team/paper/', PaperAPI.as_view()),
    path('team/paper/annotation/', AnnotationAPI.as_view()),
    path('team/paper/annotation/comment/', AnnotationCommentAPI.as_view()),
    path('team/paper/info/', PaperInfoAPI.as_view()),
    path('team/', TeamAPI.as_view()),
    path('team/paper/annotation/delete/', AnnotationDeleteAPI.as_view()),
}
urlpatterns = urlp.format_suffix_patterns(urlpatterns)
urlpatterns += router.urls

