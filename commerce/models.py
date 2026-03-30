from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    instock = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    marka = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class ProductMedia(models.Model):
    KIND_CHOICES = [
        ("image", "image"),
        ("video", "video"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.kind} for {self.product_id}"
