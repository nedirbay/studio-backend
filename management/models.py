"""Data models for the Doganlar Studio management app (Flutter `news_app`).

These mirror the local SQLite schema used by the Flutter client
(`news_app/lib/database/database_helper.dart`) so the mobile app can sync.

The app is fully self-contained: it only *references* the shared auth user
(`settings.AUTH_USER_MODEL` from the `identity` app) and never modifies any
existing app. All tables are namespaced under `management_*`.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("garaşylýar", "garaşylýar"),
        ("tassyklandy", "tassyklandy"),
        ("gutardy", "gutardy"),
        ("ýatyryldy", "ýatyryldy"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="appointments"
    )
    date = models.DateField()
    time = models.CharField(max_length=50)
    service_type = models.CharField(max_length=150)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="garaşylýar"
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self) -> str:
        return f"{self.customer.name} - {self.date} {self.time}"


class GalleryItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    image_path = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class Service(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self) -> str:
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=150)
    count = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class OrderType(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self) -> str:
        return self.name


class Expense(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.date} - {self.amount}"


class Order(models.Model):
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_type = models.ForeignKey(
        OrderType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default="pending")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.id} - {self.customer_name}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount


class OrderDay(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="days")
    date = models.DateField()
    address = models.CharField(max_length=255)
    daily_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    time = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.order_id} - {self.date}"



class OrderDayService(models.Model):
    order_day = models.ForeignKey(
        OrderDay, on_delete=models.CASCADE, related_name="services"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    count = models.IntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.order_day_id} - {self.service_id} x{self.count}"


class OrderStaff(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="management_order_assignments",
    )

    class Meta:
        unique_together = ("order", "user")

    def __str__(self) -> str:
        return f"{self.order_id} - {self.user_id}"


class OrderStaffEquipment(models.Model):
    order_staff = models.ForeignKey(
        OrderStaff, on_delete=models.CASCADE, related_name="equipments"
    )
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    received_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.order_staff_id} - {self.equipment_id} x{self.count}"


class StaffAttendance(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="attendances"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="management_attendances",
    )
    date = models.DateField()
    arrived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.order_id} - {self.user_id} @ {self.date}"


class EquipmentAssignment(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name="assignments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="management_equipments",
    )
    count = models.IntegerField(default=1)
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("equipment", "user")

    def __str__(self) -> str:
        return f"{self.equipment.name} -> {self.user_id}"
