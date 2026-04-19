from rest_framework import serializers

from commerce.models import Category, Product, ProductMedia


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=150)
    slug = serializers.CharField(max_length=150, required=False)
    icon = serializers.CharField(max_length=50, required=False)
    count = serializers.IntegerField(required=False)


class ProductMediaSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["image", "video"])
    url = serializers.CharField(max_length=255)


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=200)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    instock = serializers.BooleanField(required=False, default=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, required=False, default=5.0)
    reviews = serializers.IntegerField(required=False, default=0)
    badge = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    features = serializers.JSONField(required=False, default=list)
    specifications = serializers.JSONField(required=False, default=dict)
    marka = serializers.CharField(max_length=150, allow_null=True, required=False, allow_blank=True)
    category = serializers.IntegerField()
    media = ProductMediaSerializer(many=True, required=False, allow_null=True)
    created_at = serializers.DateTimeField(required=False)

    def validate_category(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("category not found")
        return value

    def create(self, validated_data):
        media = validated_data.pop("media", [])
        category_id = validated_data.pop("category")
        category = Category.objects.get(id=category_id)
        product = Product.objects.create(category=category, **validated_data)
        for item in media or []:
            ProductMedia.objects.create(product=product, **item)
        return product

    def update(self, instance, validated_data):
        media = validated_data.pop("media", None)
        category_id = validated_data.pop("category", None)
        if category_id is not None:
            instance.category = Category.objects.get(id=category_id)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if media is not None:
            instance.media.all().delete()
            for item in media or []:
                ProductMedia.objects.create(product=instance, **item)
        return instance

from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = ['id', 'user', 'username', 'product', 'product_name', 'subject', 'message', 'reply', 'is_read', 'created_at']
        read_only_fields = ['id', 'user', 'is_read', 'created_at']
