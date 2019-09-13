from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse  # 导入url反向解析
from django.views.generic import View  # 导入类视图
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 加密
from itsdangerous import SignatureExpired  # 过期异常类
from celery_tasks.tasks import send_register_active_email  # 异步发送邮件
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.http import HttpResponse
from .models import User, Address
from ..goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin  # 校验是否登录
from django_redis import get_redis_connection  # 连接redis数据库
import re
# Create your views here.


# 显示注册页面
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        # POST请求就用下面的方法
        # 接收数据
        username = request.POST['user_name']
        password = request.POST['pwd']
        email = request.POST['email']
        allow = request.POST['allow']

        # 数据校验
        if not all([username, password, email]):
            # all函数,在一个可迭代对象中有一项为False就返回False
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        elif allow != 'on':
            return render(request, 'register.html', {'errmsg': '未同意协议'})
        try:
            # 查看数据库中是否有重名的用户名
            userinfo = User.objects.get(username=username)
        except:
            # 如果用户名未被注册
            userinfo = None
        if userinfo:
            return render(request, 'register.html', {'errmsg': '用户名已被注册'})

        # 数据处理: 用户注册
        user = User.objects.create_user(username, email=email, password=password)
        user.is_active = 0  # 设置激活状态为未激活
        user.save()

        # 返回应答
        return redirect(reverse('goods:index'))


# 注册处理
def register_handle(request):
    # 接收数据
    username = request.POST['user_name']
    password = request.POST['pwd']
    email = request.POST['email']
    allow = request.POST['allow']

    # 数据校验
    if not all([username, password, email]):
        # all函数,在一个可迭代对象中有一项为False就返回False
        return render(request, 'register.html', {'errmsg': '数据不完整'})
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
    elif allow != 'on':
        return render(request, 'register.html', {'errmsg': '未同意协议'})
    try:
        # 查看数据库中是否有重名的用户名
        userinfo = User.objects.get(username=username)
    except:
        # 如果用户名未被注册
        userinfo = None
    if userinfo:
        return render(request, 'register.html', {'errmsg': '用户名已被注册'})

    # 数据处理: 用户注册
    user = User.objects.create_user(username, email=email, password=password)
    user.is_active = 0  # 设置激活状态为未激活
    user.save()

    # 返回应答
    return redirect(reverse('goods:index'))


# 注册 /register: 类视图函数,还需要在url中调用.as_view()方法
class RegisterView(View):
    # 显示注册页面
    def get(self, request):
        return render(request, 'register.html')

    # 注册校验
    def post(self, request):
        # POST请求就用下面的方法
        # 接收数据
        username = request.POST['user_name']
        password = request.POST['pwd']
        email = request.POST['email']
        allow = request.POST['allow']  # 是否同意协议

        # 数据校验
        if not all([username, password, email]):
            # all函数,在一个可迭代对象中有一项为False就返回False
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        elif allow != 'on':  # None 或 on
            return render(request, 'register.html', {'errmsg': '未同意协议'})
        try:
            # 查看数据库中是否有重名的用户名
            userinfo = User.objects.get(username=username)
        except:
            # 如果用户名未被注册
            userinfo = None
        if userinfo:
            return render(request, 'register.html', {'errmsg': '用户名已被注册'})

        # 数据处理: 用户注册
        # 这里调用的是django内置的创建用户方法,只有在模板中继承AbstractUser类才可以调用
        user = User.objects.create_user(username, email=email, password=password)  # 用户数据写入数据库中
        user.is_active = 0  # 设置激活状态为未激活
        user.save()

        # 发送激活邮件,包含用户id信息: http://127.0.0.1:8000/user/active/<id>
        # 激活链接中可以包含用户的多个信息

        # 加密身份信息,生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)  # 使用django自带的密钥,1小时后过期
        info = {'id': user.id}  # 这里使用上面刚创建的user.id
        # 对info进行加密,返回的是byte类型.这里必须解码否则服务器无法解析会报错
        # token会加到激活账户url链接的后面
        token = serializer.dumps(info).decode('utf8')

        # 异步发邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答
        return redirect(reverse('goods:index'))


# 激活 /active/用户的id和密文
class ActiveView(View):

    def get(self, request, token):
        # 解密获取用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 拿到用户的id
            user_id = serializer.loads(token)
            # 在数据库查找对应的用户
            user = User.objects.get(id=user_id['id'])
            user.is_active = 1  # 设置为1表示已激活
            user.save()
            # 可以改为返回自定义的欢迎页面
            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            # 激活链接过期
            print('异常: ', e)
            return HttpResponse('激活码失效请重新激活')


# 登录 /login
class LoginView(View):

    def get(self, request):
        # 显示登录页面
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            name = request.COOKIES.get('username')
            checked = 'checked'  # 自动勾选记住用户名
        else:
            name = ''
            checked = ''
        return render(request, 'login.html', {'username': name, 'checked': checked})

    def post(self, request):
        # 获取数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不能为空'})
        # 业务处理: 登录校验
        # 使用django自带的认证系统,用户和密码不存在会返回None
        user = authenticate(username=username, password=password)  # django自动校验账户密码
        # u_id = User.objects.get(username=username)  # 手动查询密码
        # pwd = u_id.password  # 查到的密码是加密状态
        # print(username, password, user, pwd, sep=', ')
        # 用户名密码正确
        if user is not None:
            if user.is_active:
                # 用户已激活
                login(request, user)  # 记录登录状态
                # 获取登录后要跳转的地址,默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                respond = redirect(next_url)  # 为了设置cookie, HttpResponseRedirect类的实例
                # 判断是否记住用户名
                remember = request.POST.get('remember')  # None on
                if remember == 'on':
                    # 设置cookie的键,值,过期时间
                    respond.set_cookie('username', username, max_age=7*24*3600)  # 记住用户名
                else:
                    respond.delete_cookie('username')  # 删除用户名
                return respond
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名密码错误
            return render(request, 'login.html', {'errmsg': '账户或密码错误'})


# 退出登录 /logout
class LogoutView(View):

    def get(self, request):
        # django会自动清除用户的session信息
        logout(request)
        # 退出后跳转到首页
        return redirect(reverse('goods:index'))


# 用户中心,个人信息 /user
class UserInfoView(LoginRequiredMixin, View):
    # 注意!只有使用django内置的登录系统User.objects.create_user()创建用户,才可以使用内置认证系统login_required()
    # 用户信息中心,类继承是从前往后调用,前面有的方法就不会向后调用
    def get(self, request):
        # page=user 选中的页面显示黄色字体
        # request.user
        # django每次在调用视图的时候,都会把request.user也传递给模板,所以在模板中可以直接使用user
        # request.user.is_authenticated()方法
        # 如果未登录->user是AnonymousUser类的实例,返回False
        # 如果用户登录->user是User类的实例,返回True
        # 两个类中都有is_authenticated()方法,只是返回值不同

        # 显示个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 显示最近浏览
        # 获取用户的最近浏览
        # from redis import StrictRedis
        # sr = StrictRedis(host='192.168.177.128', port=6379, db=9)
        con = get_redis_connection('default')  # 使用这个方法可以快速连接默认的缓存数据库
        history_key = 'history_{}'.format(user.id)  # 拼接出要查询的用户id
        # 获取用户浏览过的前5个商品
        sku_ids = con.lrange(history_key, 0, 4)
        # 按顺序获取用户的浏览记录
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_ls': goods_li}
        return render(request, 'user_center_info.html', context)


# 全部订单 /user/order
class UserOrderView(LoginRequiredMixin, View):

    def get(self, request):
        # page=order
        return render(request, 'user_center_order.html', {'page': 'order'})


# (<class 'apps.user.views.UserOrderView'>, <class 'utils.mixin.LoginRequiredMixin'>,
# <class 'django.views.generic.base.View'>, <class 'object'>)
# 所以要调用View里面的as_view()方法,View需要写在后面
# print(UserOrderView.__mro__)


# 收货地址 /user/address
class AddressView(LoginRequiredMixin, View):

    def get(self, request):
        # page=address
        user = request.user
        # try:
        #     # 查询数据库中是否有默认地址
        #     address = Address.objects.get(user=request.user, is_default=True)
        # except Exception as er:
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 数据校验
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3|4|5|6|7|8|9][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号码格式不正确'})
        # 添加地址
        user = request.user
        # try:
        #     # 查询数据库中是否有默认地址
        #     # address = Address.objects.get(user=request.user, is_default=True)
        #     Address.objects.get(user=user, is_default=True)
        #     # 如果有默认地址,那么新加的地址就不会是默认地址
        #     is_default = False
        # except Exception as er:
        #     print(er)
        #     # address = None
        #     is_default = True
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address'))
