from django.db import models
from django.core.validators import MinValueValidator
from .validators import validate_product_img_size
from django.conf import settings
import uuid
# Create your models here.


class Category(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']


class Product(models.Model):
    title = models.CharField(max_length=255)
    # slug=models.SlugField()
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1),])
    inventory = models.IntegerField()
    last_update = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )

    def __str__(self) -> str:
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='store/images',
                              validators=[validate_product_img_size,])


class CategoryImage(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='store/images',
                              validators=[validate_product_img_size,])


class Order(models.Model):

    placed_at = models.DateTimeField(auto_now_add=True)

    is_delivered = models.BooleanField(default=False)
    is_shipped = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    total_price = models.DecimalField(
        default=0.00, max_digits=10, decimal_places=2)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.PROTECT)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


class Cart(models.Model):
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)])

    class Meta:
        # No duplicated records for the same product in the same cart
        # if user want multiple same product just increase the quantity.
        unique_together = [['cart', 'product']]


class Feedback(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=150, null=True, blank=True)
    mobile = models.CharField(max_length=12, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name
