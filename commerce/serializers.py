from rest_framework import serializers

from commerce.models import Category, Product, ProductMedia


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=150)


class ProductMediaSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["image", "video"])
    url = serializers.CharField(max_length=255)


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=200)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    instock = serializers.BooleanField(required=False, default=True)
    created_at = serializers.DateTimeField(required=False)
    category = serializers.IntegerField()
    marka = serializers.CharField(max_length=150, allow_null=True, required=False, allow_blank=True)
    media = ProductMediaSerializer(many=True, required=False, allow_null=True)

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
