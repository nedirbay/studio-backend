from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, null=True, blank=True)
    main_image = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class BlogMedia(models.Model):
    TYPE_CHOICES = [
        ("image", "image"),
        ("video", "video"),
    ]
    
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=10, choices=TYPE_CHOICES)
    url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.kind} for {self.blog_id}"
