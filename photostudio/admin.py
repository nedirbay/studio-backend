from django.contrib import admin
from .models import (
    PhotoCategory,
    PhotoBlog,
    PhotoMedia,
    PhotoReel,
    PhotoReelTag,
    PhotoReelLike,
    PhotoReelComment,
    PhotoReelShare,
)


@admin.register(PhotoCategory)
class PhotoCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)


class PhotoMediaInline(admin.TabularInline):
    model = PhotoMedia
    extra = 1


@admin.register(PhotoBlog)
class PhotoBlogAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date", "created_at")
    list_filter = ("category", "date")
    search_fields = ("title", "description")
    inlines = [PhotoMediaInline]


class PhotoReelTagInline(admin.TabularInline):
    model = PhotoReelTag
    extra = 1


@admin.register(PhotoReel)
class PhotoReelAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "kind", "category", "author", "views", "is_published", "created_at")
    list_filter = ("kind", "category", "is_published")
    search_fields = ("title", "description")
    inlines = [PhotoReelTagInline]


@admin.register(PhotoReelLike)
class PhotoReelLikeAdmin(admin.ModelAdmin):
    list_display = ("reel", "user", "created_at")


@admin.register(PhotoReelComment)
class PhotoReelCommentAdmin(admin.ModelAdmin):
    list_display = ("reel", "user", "text", "created_at")
    search_fields = ("text",)


@admin.register(PhotoReelShare)
class PhotoReelShareAdmin(admin.ModelAdmin):
    list_display = ("reel", "user", "channel", "created_at")
