from django.contrib import admin
from .models import GoodsType, IndexGoodsBanner, GoodsSKU, Goods
from django.core.cache import cache
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    """admin模型管理器类"""

    def save_model(self, request, obj, form, change):
        """修改数据"""
        super(BaseModelAdmin, self).save_model(request, obj, form, change)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除数据"""
        super(BaseModelAdmin, self).delete_model(request, obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')


class IndexGoodsBannerModelAdmix(BaseModelAdmin):
    list_display = ('index', 'sku')
    list_display_links = ('index', 'sku')


admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerModelAdmix)
admin.site.register(GoodsSKU, BaseModelAdmin)
admin.site.register(Goods, BaseModelAdmin)
