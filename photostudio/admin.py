from django.contrib import admin
from .models import PhotoCategory, PhotoBlog, PhotoMedia

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
