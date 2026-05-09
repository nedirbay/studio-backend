from django.contrib import admin

from commerce.models import Category, Product, ProductMedia, Brand, Order, OrderItem


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


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone_number", "total_price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone_number")
    inlines = [OrderItemInline]
