from django.urls import path
from rest_framework import routers
from rest_framework import urlpatterns as urlp

from .views.UserAPI import UserAPI
from .views.LoginAPI import LoginAPI

router = routers.DefaultRouter()
urlpatterns = {
    path('user/', UserAPI.as_view()),
    path('login/', LoginAPI.as_view()),
}
urlpatterns = urlp.format_suffix_patterns(urlpatterns)
urlpatterns += router.urls

