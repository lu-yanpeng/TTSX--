from django.conf import settings
from celery import Celery  # 导入celery,注意版本为4.1.1否则无法使用
from django.core.mail import send_mail  # 导入发送邮件的函数
from django.template import loader, RequestContext  # 加载模板
import time
# 在ubuntu中 pip install py3fdfs 不然会有很多错误

# 输入下面代码,让django把设置先预加载一遍,这里只需要在服务器上预加载就行了
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()
# 加载模型类要写在这几句的后面,否则报错
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# 创建celery类的对象,第一个参数可以随便填,但建议写当前文件的路径,第二个参数指定一个中间人数据库
app = Celery('celery_tasks.tasks', broker='redis://192.168.177.128:6379/8')


# 发送激活邮件
@app.task
def send_register_active_email(to_email, username, token):
    subject = '天天生鲜欢迎信息'  # 邮件标题
    message = ''  # 邮件正文,如果包含html内容就不能放在这里发送,否则会直接发送字符串
    sender = settings.EMAIL_FROM  # 发件人邮箱
    receiver = [to_email]  # 收件人,可以同时发给多人
    # 正文内容包含html,请用html_message参数传递
    html_context = '<h1>{0}, 欢迎注册天天生鲜,请点击<br/><a href="http://127.0.0.1:8000/user/active/{1}">' \
                   'http://127.0.0.1:8000/user/active/{1}</a>激活账户</h1>'.format(username, token)
    send_mail(subject, message, sender, receiver, html_message=html_context)  # 要按顺序传递
    print('windows')
    time.sleep(5)


# 产生首页静态页面
@app.task
def generate_static_index_html():
    """首页显示"""
    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type_n in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=types, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=types, display_type=0).order_by('index')
        # 动态增加属性,增加首页分类商品的图片和文字信息
        # 给每一个商品种类加上分类商品的信息
        type_n.image_banners = image_banners
        type_n.title_banners = title_banners

    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners}

    # 使用模板生成对应的静态文件
    # 1.加载模板文件
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)
    # 3.保存文件
    # 拼接要保存的路径
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
