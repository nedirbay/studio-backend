from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    icon = models.CharField(max_length=50, null=True, blank=True)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    instock = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    reviews = models.IntegerField(default=0)
    badge = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    features = models.JSONField(default=list, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    marka = models.CharField(max_length=150, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    logo_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_reviews")
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name="user_reviews")
    rating = models.IntegerField(default=5)
    title = models.CharField(max_length=150, blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product rating and review count
        all_reviews = Review.objects.filter(product=self.product)
        count = all_reviews.count()
        avg_rating = sum([r.rating for r in all_reviews]) / count if count > 0 else 5.0
        
        self.product.rating = avg_rating
        self.product.reviews = count
        self.product.save(update_fields=['rating', 'reviews'])

class ContactMessage(models.Model):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, related_name="contact_messages", null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="contact_messages", null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    reply = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user.username if self.user else 'Guest'} - {self.subject}"
