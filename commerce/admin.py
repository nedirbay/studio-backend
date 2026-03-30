from django.contrib import admin

from commerce.models import Category, Product, ProductMedia


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "instock", "category", "created_at")
    list_filter = ("category", "instock")
    search_fields = ("name", "marka")
    inlines = [ProductMediaInline]
