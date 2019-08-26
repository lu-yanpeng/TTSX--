from django.conf.urls import url
from .views import RegisterView, ActiveView, LoginView
from . import views

urlpatterns = [
    # url(r'^register/?$', views.register, name='register'),  # 注册
    # url(r'^register_handle$', views.register_handle, name='register_handle'),  # 注册校验
    url(r'^register/?$', RegisterView.as_view(), name='register'),  # 使用类视图函数返回应答
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活:捕获用户信息
    url(r'^login$', LoginView.as_view(), name='login'),  # 显示登录页面
]
