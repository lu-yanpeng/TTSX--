from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),  # 访问django的首页
]
