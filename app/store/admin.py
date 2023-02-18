from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, urlencode
from django.db.models import Count
from . import models
from typing import Sequence
# Register your models here.


class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    readonly_fields: Sequence[str] = ['thumbnail']

    def thumbnail(self, instance):
        if instance.image.name != '':
            return format_html(f'<img src="{instance.image.url}" class="thumbnail">')
        return ''

    class Media:
        css = {
            'all': ['store/style.css']
        }


class CategoryImageInline(admin.StackedInline):
    model = models.CategoryImage
    readonly_fields: Sequence[str] = ['thumbnail']
    max_num:int=1

    def thumbnail(self, instance):
        if instance.image.name != '':
            return format_html(f'<img src="{instance.image.url}" class="thumbnail">')
        return ''

@admin.register(models.Product)
class Product(admin.ModelAdmin):
    autocomplete_fields = ['category']
    inlines = [ProductImageInline]
    list_display = ['id', 'title', 'unit_price', 'category_title']
    list_editable = ['unit_price',]
    list_filter = ['last_update', 'category',]
    list_per_page: int = 20
    search_fields: Sequence[str] = ['title', 'id',]
    list_select_related = ['category',]

    def category_title(self, product):
        return product.category.title


@admin.register(models.Category)
class categoryAdmin(admin.ModelAdmin):
    """
    Actually we don't have product_count 
    field in our database , so we just 
    create a method for display product count,
    : category table does't have that field 
    since we annotate that field by overriding
    get_queryset method in ModelAdmin class

    """
    list_display = ['title', 'product_count']
    search_fields = ['title']
    inlines=[CategoryImageInline]

    @admin.display(ordering='product_count')
    def product_count(self, category):
        # url=reverse('admin:app_model_page)
        url = (reverse('admin:store_product_changelist') +
               '?' +
               urlencode({
                   'category__id': str(category.id)
               }))

        return format_html(f'<a href="{url}">{category.product_count}</a>')

    # overriding get_queryset method from ModelAdmin class for calculate count of product in a category
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('products')
        )
