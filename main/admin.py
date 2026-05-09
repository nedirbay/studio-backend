from django.contrib import admin
from .models import (
    Customer, Appointment, Equipment, Order, OrderDay, 
    OrderStaff, Expense, OrderType, Banner, Promo
)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone")

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "date", "time", "service_type", "status")
    list_filter = ("status", "date")
    search_fields = ("customer__name", "service_type")

@admin.register(OrderType)
class OrderTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)

class OrderDayInline(admin.TabularInline):
    model = OrderDay
    extra = 1

class OrderStaffInline(admin.TabularInline):
    model = OrderStaff
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "customer_phone", "total_amount", "paid_amount", "created_at")
    search_fields = ("customer_name", "customer_phone")
    inlines = [OrderDayInline, OrderStaffInline]

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "count")

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "amount", "description")
    list_filter = ("date",)

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "created_at")
    search_fields = ("title", "subtitle")

@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "badge", "created_at")
    search_fields = ("title", "subtitle")
