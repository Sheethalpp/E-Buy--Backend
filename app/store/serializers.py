from rest_framework import serializers
from . import models
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()


class ProductImageSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        product_id = self.context['product_id']
        return models.ProductImage.objects.create(product_id=product_id, **validated_data)

    class Meta:
        model = models.ProductImage
        fields = ['id', 'image']


class CategoryImageSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        product_id = self.context['category_id']
        return models.CategoryImage.objects.create(product_id=product_id, **validated_data)

    class Meta:
        model = models.CategoryImage
        fields = ['id', 'image']


class CategorySerializer(serializers.ModelSerializer):
    # This field a custom field , so read_only should be True, dont need to send it ti the server
    product_count = serializers.IntegerField(read_only=True)
    images = CategoryImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Category
        fields = ['id', 'title', 'product_count', 'images']
        # read_only_fields = ['product_count']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()

    class Meta:
        model = models.Product
        fields = ['id', 'title', 'last_update', 'description', 'inventory',
                  'unit_price', 'price_with_tax', 'category', 'images']

    # CustomSerializerField
    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')

    def calculate_tax(self, product: models.Product):
        return round((product.unit_price * Decimal(1.1)), 2)


class SimpleProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Product
        fields = ['id', 'title', 'unit_price', 'images',]


class CartItemSerializer(serializers.ModelSerializer):

    # product = ProductSerializer()
    product = SimpleProductSerializer()
    # custom field for show total price
    total_price = serializers.SerializerMethodField()

    # define custom method for show total price
    # get_total_price name is a convention : get_ followed by method_name
    def get_total_price(self, cart_item: models.CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = models.CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    # We dont want to send id to server, just read from server
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    # calculate total price of a cart
    def get_total_price(self, cart: models.Cart):
        return sum([(item.quantity * item.product.unit_price) for item in cart.items.all()])

    class Meta:
        model = models.Cart
        fields = ['id', 'items', 'total_price']


class AddCartItemSerializer(serializers.ModelSerializer):
    # product_id declaration
    product_id = serializers.IntegerField()

    # Validating product_id, if it is not exists then rise an error message
    def validate_product_id(self, value):
        if not models.Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No products with given id')
        return value

    # Override, create a new cartitem or update an existing one
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = models.CartItem.objects.get(
                cart_id=cart_id, product_id=product_id)
            # update an item
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item

        except models.CartItem.DoesNotExist:
            # create an item
            self.instance = models.CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)

        return self.instance

    class Meta:
        model = models.CartItem
        fields = ['id', 'product_id', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ['quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()

    class Meta:
        model = models.OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity']


# FIXME: 94 quries executing while send get
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    # payment = PaymentSerializer(many=True)

    class Meta:
        model = models.Order
        fields = ['id', 'placed_at', 'total_price', 'items',
                  'is_delivered', 'is_shipped', 'is_cancelled',]


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = ['is_delivered', 'is_cancelled', 'is_shipped']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    # payment = PaymentSerializer()

    def validate_cart_id(self, cart_id):
        if not models.Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('Cart does not exists')
        if models.CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('Cart is empty')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            # Get cart id from validated data; from client side
            cart_id = self.validated_data['cart_id']
            # Fetch customer using user_id from request ; set it in views
            # customer = customer.objects.get(
            #     user_id=self.context['user_id'])
            user_id = self.context['user_id']
            # print('user',user_id)

            cart_items = models.CartItem.objects \
                .select_related('product') \
                .filter(cart_id=cart_id)

            total_price = sum([(item.quantity * item.product.unit_price)
                               for item in cart_items])
            # print('toatalprice', total_price)
            # Create an order
            order = models.Order.objects.create(
                user_id=user_id, total_price=total_price)

            # create payment child table
            # payment = Payment.objects.create(
            #     order=order, **self.validated_data['payment'])

            # create order item list
            order_items = [
                models.OrderItem(
                    order=order,
                    product=item.product,
                    unit_price=item.product.unit_price,
                    quantity=item.quantity

                ) for item in cart_items
            ]

            # create order items in db
            models.OrderItem.objects.bulk_create(order_items)
            # delete cart
            models.Cart.objects.filter(pk=cart_id).delete()

            # send signal
            # order_created.send_robust(sender=self.__class__, order=order)

            return order


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Feedback
        fields = ['name', 'email', 'mobile', 'comment',]
