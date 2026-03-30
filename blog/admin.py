from django.contrib import admin

from blog.models import BlogMedia, BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "created_at")
    search_fields = ("title",)
    date_hierarchy = "date"


@admin.register(BlogMedia)
class BlogMediaAdmin(admin.ModelAdmin):
    list_display = ("blog", "kind", "url", "created_at")
    list_filter = ("kind",)
