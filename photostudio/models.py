from django.db import models


class PhotoStudioVideo(models.Model):
    HLS_STATUS_CHOICES = [
        ("pending", "pending"),
        ("processing", "processing"),
        ("ready", "ready"),
        ("failed", "failed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail_image = models.FileField(upload_to="photostudio/videos/thumbnails/")
    video = models.FileField(upload_to="photostudio/videos/")
    hls_playlist = models.CharField(max_length=500, blank=True)
    hls_status = models.CharField(max_length=20, choices=HLS_STATUS_CHOICES, default="pending")
    hls_error = models.TextField(blank=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-create_at"]

    def __str__(self) -> str:
        return self.title


class PhotoStudioImage(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail_image = models.FileField(upload_to="photostudio/images/thumbnails/")
    image = models.FileField(upload_to="photostudio/images/")
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-create_at"]

    def __str__(self) -> str:
        return self.title
