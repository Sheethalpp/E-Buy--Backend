from django.db.models import Count
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
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


class CartViewSet(CreateModelMixin,  # create cart with id, pass post request with empty ,
                  RetrieveModelMixin,  # ../carts/id/ retrieving a specific cart
                  DestroyModelMixin,  # delete a 'cart/id/'
                  GenericViewSet
                  ):

    # prefetch_related used for fetch child table items, in foreignkey realation we use select_related
    queryset = models.Cart.objects.prefetch_related('items__product').all()
    serializer_class = serializers.CartSerializer


class CartItemViewSet(ModelViewSet):
    # must be lowercase in the list
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return serializers.UpdateCartItemSerializer
        return serializers.CartItemSerializer

    def get_queryset(self):
        return models.CartItem.objects \
            .filter(cart_id=self.kwargs['cart_pk']) \
            .select_related('product')

    # cart_pk value from url; add to context dict ; so we can access this value in serializer for creating custom save methode(override save methode)
    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch',
                         'delete', 'head', 'options']

    # def get_permissions(self):
    #     if self.request.method in ['PATCH', 'DELETE']:
    #         return [IsAdminUser()]
    #     return [IsAuthenticated()]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return serializers.UpdateOrderSerializer
        return serializers.OrderSerializer

    def get_queryset(self):
        user = self.request.user
        # admin or staff are able to see all orders
        if user.is_staff:
            return models.Order.objects.prefetch_related('items').all().order_by('-id')

        # customer_id = Customer.objects \
        #     .only('id').get(user_id=user.id)
        user_id = self.request.user.id

        return models.Order.objects.filter(user_id=user_id).order_by('-id')

    def create(self, request, *args, **kwargs):
        serializer = serializers.CreateOrderSerializer(
            data=request.data,
            context={'user_id': self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        # deserialize the saved order using order serializer ; CreateOrderSerializer only for creating and returning with cart_id
        serializer = serializers.OrderSerializer(order)
        return Response(serializer.data)


class FeedbackViewSet(ModelViewSet):
    http_method_names=['post']
    serializer_class = serializers.FeedbackSerializer
    queryset = models.Feedback.objects.all()
