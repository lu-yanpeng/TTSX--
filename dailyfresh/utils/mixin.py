from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    # 校验是否登录,没有登录会自动跳转到settings.LOGIN_URL
    @classmethod
    def as_view(cls, **initkwargs):
        # 这里用到mro,类的继承顺序
        # 调用父类的as_view方法,这里的父类是View,相当于向后调用了View的as_view方法
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)
