from django import views
from django.urls import path, include
from rest_framework_nested import routers
from .import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')
router.register('categories', views.CategoryViewSet, basename='categories')
router.register('carts', viewset=views.CartViewSet, basename='carts')
router.register('orders', viewset=views.OrderViewSet, basename='orders')
router.register('feedback', viewset=views.FeedbackViewSet, basename='feedback')


carts_router = routers.NestedDefaultRouter(
    parent_router=router, parent_prefix='carts', lookup='cart')
carts_router.register(
    prefix='items', viewset=views.CartItemViewSet, basename='cart-items')


urlpatterns = router.urls + carts_router.urls   
