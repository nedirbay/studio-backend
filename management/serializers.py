"""DRF model serializers for the management app.

The function-based views build Flutter-shaped JSON by hand (see `views.py`), but
these serializers are provided for reuse (e.g. admin tooling, future DRF
viewsets, or schema generation) and as a single source of truth for field sets.
"""

from rest_framework import serializers

from .models import (
    Appointment,
    Customer,
    Equipment,
    EquipmentAssignment,
    Expense,
    GalleryItem,
    Order,
    OrderDay,
    OrderStaff,
    OrderType,
    Service,
    StaffAttendance,
)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "email", "created_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_phone",
            "date",
            "time",
            "service_type",
            "status",
            "notes",
            "created_at",
        ]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["id", "name", "count"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name"]


class OrderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderType
        fields = ["id", "name"]


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ["id", "amount", "date", "description", "created_at"]


class GalleryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryItem
        fields = ["id", "title", "description", "image_path", "category", "created_at"]


class OrderDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDay
        fields = ["id", "order", "date", "address", "daily_price", "time"]


class OrderStaffSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = OrderStaff
        fields = ["id", "order", "user", "user_name"]


class OrderSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    days = OrderDaySerializer(many=True, read_only=True)
    staff = OrderStaffSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "customer_phone",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "order_type",
            "created_at",
            "days",
            "staff",
        ]


class EquipmentAssignmentSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source="equipment.name", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = EquipmentAssignment
        fields = [
            "id",
            "equipment",
            "equipment_name",
            "user",
            "user_name",
            "count",
            "assigned_at",
        ]


class StaffAttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = StaffAttendance
        fields = ["id", "order", "user", "user_name", "date", "arrived_at"]
