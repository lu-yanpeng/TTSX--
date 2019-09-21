from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from .models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django.core.cache import cache  # 设置缓存
# Create your views here.


# 首页 127.0.0.1:8000
class IndexView(View):
    """首页"""

    def get(self, request):
        """首页显示"""
        # 取不到的话返回None,取到就返回缓存中的字典
        context = cache.get('index_page_data')
        if context is None:
            # 缓存中没有数据
            # print('设置缓存')
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
            # 组织模板
            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 根据CACHES,设置缓存
            # key value timeout
            cache.set('index_page_data', context, 3600)

        # 获取用户购物车中的商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_{}id'.format(user.id)
            # 查询cart_key对应的哈希类型的属性数量
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context.update(cart_count=cart_count)  # 设置购物车中商品的数量

        return render(request, 'index.html', context)
