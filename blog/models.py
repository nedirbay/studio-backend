from django.db import models
from django.utils import timezone


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    main_image = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

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
