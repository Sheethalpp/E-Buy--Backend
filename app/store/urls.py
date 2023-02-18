from django import views
from django.urls import path, include
from rest_framework_nested import routers
from .import views

router=routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')
router.register('categories', views.CategoryViewSet, basename='categories')


urlpatterns = router.urls