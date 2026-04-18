from django.contrib import admin
from .models import Banner, Promo

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "created_at")
    search_fields = ("title", "subtitle")

@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "badge", "created_at")
    search_fields = ("title", "subtitle")
