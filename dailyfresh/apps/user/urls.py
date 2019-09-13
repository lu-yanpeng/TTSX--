from django.conf.urls import url
from .views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView
from django.contrib.auth.decorators import login_required  # 登录校验装饰器
from . import views

urlpatterns = [
    # url(r'^register/?$', views.register, name='register'),  # 注册
    # url(r'^register_handle$', views.register_handle, name='register_handle'),  # 注册校验
    url(r'^register/?$', RegisterView.as_view(), name='register'),  # 使用类视图函数返回应答
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活:捕获用户信息
    url(r'^login$', LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', LogoutView.as_view(), name='logout'),  # 退出登录
    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户中心,用登录装饰器包起来判断是否登录
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户订单
    # url(r'^address$', login_required(AddressView.as_view()), name='address'),  # 用户地址
    url(r'^$', UserInfoView.as_view(), name='user'),
    url(r'^order$', UserOrderView.as_view(), name='order'),
    url(r'^address$', AddressView.as_view(), name='address'),
]
