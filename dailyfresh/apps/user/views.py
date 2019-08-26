from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse  # 导入url反向解析
from django.views.generic import View  # 导入类视图
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 加密
from itsdangerous import SignatureExpired  # 过期异常类
from celery_tasks.tasks import send_register_active_email  # 异步发送邮件
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.http import HttpResponse
from .models import User
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


# 注册: 类视图函数,还需要在url中调用.as_view()方法
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
        allow = request.POST['allow']

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
        # 这里调用的是django内置的创建用户方法,只有继承AbstractUser类才可以调用
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


# 激活
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
            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            # 激活链接过期
            print('异常: ', e)
            return HttpResponse('激活码失效请重新激活')


# 登录
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
        user = authenticate(username=username, password=password)

        # u_id = User.objects.get(username=username)
        # pwd = u_id.password  # 查到的密码是加密状态
        # print(username, password, user, pwd, sep=', ')

        # 用户名密码正确
        if user is not None:
            if user.is_active:
                # 用户已激活
                login(request, user)  # 记录登录状态
                respond = redirect(reverse('goods:index'))  # 为了设置cookie
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
