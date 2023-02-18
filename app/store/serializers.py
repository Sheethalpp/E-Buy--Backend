from rest_framework import serializers
from . import models
from decimal import Decimal


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
