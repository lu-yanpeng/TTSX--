from django.conf import settings
from celery import Celery  # 导入celery,注意版本为4.1.1否则无法使用
from django.core.mail import send_mail  # 导入发送邮件的函数
import time

# 输入下面代码,让django把设置先预加载一遍,这里只需要在服务器上预加载就行了
# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

# # 创建celery类的对象,第一个参数可以随便填,但建议写当前文件的路径,第二个参数指定一个中间人数据库
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
