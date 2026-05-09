from django.db import models
from django.utils import timezone

class PhotoCategory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

class PhotoBlog(models.Model):
    category = models.ForeignKey(PhotoCategory, on_delete=models.CASCADE, related_name="blogs")
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

class PhotoMedia(models.Model):
    TYPE_CHOICES = [
        ("image", "image"),
        ("video", "video"),
    ]
    
    blog = models.ForeignKey(PhotoBlog, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=10, choices=TYPE_CHOICES)
    url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.kind} for {self.blog.title}"

