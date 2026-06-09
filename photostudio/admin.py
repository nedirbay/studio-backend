from django.contrib import admin

from .models import PhotoStudioImage, PhotoStudioVideo


@admin.register(PhotoStudioVideo)
class PhotoStudioVideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "hls_status", "create_at")
    list_filter = ("hls_status",)
    search_fields = ("title", "description")
    ordering = ("-create_at",)


@admin.register(PhotoStudioImage)
class PhotoStudioImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "create_at")
    search_fields = ("title", "description")
    ordering = ("-create_at",)
