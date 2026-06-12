from django.contrib import admin

from .models import (
    Appointment,
    Customer,
    Equipment,
    EquipmentAssignment,
    Expense,
    GalleryItem,
    Order,
    OrderDay,
    OrderDayEquipment,
    OrderDayService,
    OrderStaff,
    OrderStaffEquipment,
    OrderType,
    Service,
    StaffAttendance,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "date", "time", "service_type", "status")
    list_filter = ("status", "date")
    search_fields = ("customer__name", "service_type")


class OrderDayEquipmentInline(admin.TabularInline):
    model = OrderDayEquipment
    extra = 0


class OrderDayServiceInline(admin.TabularInline):
    model = OrderDayService
    extra = 0


@admin.register(OrderDay)
class OrderDayAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "date", "address", "daily_price")
    inlines = [OrderDayEquipmentInline, OrderDayServiceInline]


class OrderDayInline(admin.TabularInline):
    model = OrderDay
    extra = 0


class OrderStaffInline(admin.TabularInline):
    model = OrderStaff
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "customer_phone", "total_amount", "paid_amount", "created_at")
    search_fields = ("customer_name", "customer_phone")
    inlines = [OrderDayInline, OrderStaffInline]


class OrderStaffEquipmentInline(admin.TabularInline):
    model = OrderStaffEquipment
    extra = 0


@admin.register(OrderStaff)
class OrderStaffAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "user")
    inlines = [OrderStaffEquipmentInline]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "count")
    search_fields = ("name",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "date", "description")
    list_filter = ("date",)


@admin.register(EquipmentAssignment)
class EquipmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "equipment", "user", "count", "assigned_at")


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "user", "date", "arrived_at")
    list_filter = ("date",)


admin.site.register(GalleryItem)
admin.site.register(Service)
admin.site.register(OrderType)
