from django.urls import path
from rest_framework import routers
from rest_framework import urlpatterns as urlp

from .views.UserAPI import UserAPI
from .views.LoginAPI import LoginAPI
from .views.PaperAPI import PaperAPI
from .views.PaperDeleteAPI import PaperDeleteAPI
from .views.AnnotationAPI import AnnotationAPI
from .views.AnnotationCommentAPI import AnnotationCommentAPI
from .views.AnnotationCommentDeleteAPI import AnnotationCommentDeleteAPI
from .views.PaperInfoAPI import PaperInfoAPI
from .views.TeamAPI import TeamAPI
from .views.AnnotationDeleteAPI import AnnotationDeleteAPI
from .views.TagAPI import TagAPI
from .views.WatchAPI import WatchAPI
from .views.PaperOpenAPI import PaperOpenAPI
from .views.AnnotationOpenAPI import AnnotationOpenAPI

router = routers.DefaultRouter()
urlpatterns = {
    path('team/user/', UserAPI.as_view()),
    path('team/login/', LoginAPI.as_view()),
    path('team/paper/', PaperAPI.as_view()),
    path('team/paper/delete/', PaperDeleteAPI.as_view()),
    path('team/paper/annotation/', AnnotationAPI.as_view()),
    path('team/paper/annotation/comment/', AnnotationCommentAPI.as_view()),
    path('team/paper/annotation/comment/delete/', AnnotationCommentDeleteAPI.as_view()),
    path('team/paper/info/', PaperInfoAPI.as_view()),
    path('team/', TeamAPI.as_view()),
    path('team/paper/annotation/delete/', AnnotationDeleteAPI.as_view()),
    path('team/tag/', TagAPI.as_view()),
    path('team/paper/watch/', WatchAPI.as_view()),
    path('team/paper/open/', PaperOpenAPI.as_view()),
    path('team/paper/annotation/open/', AnnotationOpenAPI.as_view()),
}
urlpatterns = urlp.format_suffix_patterns(urlpatterns)
urlpatterns += router.urls

