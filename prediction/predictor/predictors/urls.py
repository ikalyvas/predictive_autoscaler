from django.urls import re_path
from .views import predict, metrics

urlpatterns = [
    re_path(r'^$', predict),
    re_path(r'^metrics/', metrics),
]
