from django.db.models import Count
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend


from . import models
from . import serializers
from .permissions import IsAdminOrReadOnly
from .filters import ProductFilter

# Create your views here.


class ProductViewSet(ModelViewSet):

    queryset = models.Product.objects.prefetch_related('images').all()
    serializer_class = serializers.ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    # Using django filter library for filtering product based on the collection
    # define filterbackend and filteing logic in a class
    # e.g: url--> http://127.0.0.1:8000/store/products/?collection_id=4 , filtering query is-->products/?collection_id=4
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    # sorting based on unit_price and last_update
    ordering_fields = ['unit_price', 'last_update']
    # pagination_class = DefaultPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if models.Product.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': "Can't delete , product associated with an order"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class CategoryViewSet(ModelViewSet):

    serializer_class = serializers.CategorySerializer
    queryset = models.Category.objects.annotate(
        product_count=Count('products')).all().order_by('title')
    permission_classes = [IsAdminOrReadOnly]

    # Override
    # def destroy(self, request, *args, **kwargs):
    #     collection = get_object_or_404(Collection.objects.annotate(
    #         product_count=Count('products')), pk=kwargs['pk'])

    #     if collection.products.count() > 0:
    #         return Response({'error': "Can't delete , it includes one or more products"},
    #                         status=status.HTTP_405_METHOD_NOT_ALLOWED)
    #     return super().destroy(request, *args, **kwargs)
