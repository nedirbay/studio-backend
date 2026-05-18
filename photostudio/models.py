from django.db import models
from django.utils import timezone
from django.conf import settings


class PhotoCategory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class PhotoCollection(models.Model):
    KIND_CHOICES = [
        ("video", "video"),
        ("image", "image"),
    ]

    category = models.ForeignKey(
        PhotoCategory,
        on_delete=models.SET_NULL,
        related_name="collections",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="video")
    cover_url = models.CharField(max_length=500, blank=True)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def items_count(self) -> int:
        return self.reels.filter(is_published=True).count()


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


# ---------------------------------------------------------------------------
# Reels / TikTok-style feed
# ---------------------------------------------------------------------------


class PhotoReel(models.Model):
    KIND_CHOICES = [
        ("video", "video"),
        ("image", "image"),
    ]

    category = models.ForeignKey(
        PhotoCategory,
        on_delete=models.SET_NULL,
        related_name="reels",
        null=True,
        blank=True,
    )
    collection = models.ForeignKey(
        PhotoCollection,
        on_delete=models.SET_NULL,
        related_name="reels",
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reels",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="video")
    media_url = models.CharField(max_length=500)
    thumbnail_url = models.CharField(max_length=500, blank=True)
    stream_url = models.CharField(max_length=500, blank=True, help_text="HLS/DASH stream url for video")
    duration = models.FloatField(default=0, help_text="duration in seconds")
    views = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    music_title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title or f"Reel #{self.pk}"

    @property
    def likes_count(self) -> int:
        return self.likes.count()

    @property
    def comments_count(self) -> int:
        return self.comments.count()

    @property
    def shares_count(self) -> int:
        return self.shares.count()


class PhotoReelTag(models.Model):
    reel = models.ForeignKey(PhotoReel, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=80)

    def __str__(self) -> str:
        return f"#{self.name}"


class PhotoReelLike(models.Model):
    reel = models.ForeignKey(PhotoReel, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reel_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("reel", "user")

    def __str__(self) -> str:
        return f"like {self.user_id} -> {self.reel_id}"


class PhotoReelComment(models.Model):
    reel = models.ForeignKey(PhotoReel, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reel_comments")
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name="replies", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"comment {self.user_id} -> {self.reel_id}"


class PhotoReelShare(models.Model):
    reel = models.ForeignKey(PhotoReel, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="reel_shares", null=True, blank=True)
    channel = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"share {self.reel_id}"
