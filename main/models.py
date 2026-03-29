from django.db import models
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class User(models.Model):
    name = models.CharField(max_length=150)
    token = models.CharField(max_length=255, unique=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    phone = models.CharField(max_length=50, null=True, blank=True)
    avatar_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("garaşylýar", "garaşylýar"),
        ("tassyklandy", "tassyklandy"),
        ("gutardy", "gutardy"),
        ("ýatyryldy", "ýatyryldy"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="appointments")
    date = models.DateField()
    time = models.CharField(max_length=50)
    service_type = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="garaşylýar")
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.customer.name} - {self.date} {self.time}"


class GalleryItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    image_path = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.title


class Equipment(models.Model):
    name = models.CharField(max_length=150)
    count = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_type_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Order {self.id} - {self.customer_name}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount


class OrderDay(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="days")
    date = models.DateField()
    address = models.CharField(max_length=255)
    daily_price = models.DecimalField(max_digits=12, decimal_places=2)
    time = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.order_id} - {self.date}"


class OrderStaff(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_assignments")
    role = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = ("order", "user")

    def __str__(self) -> str:
        return f"{self.order_id} - {self.user_id}"


class Expense(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.date} - {self.amount}"


class EquipmentAssignment(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="equipments")
    count = models.IntegerField(default=1)
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("equipment", "user")

    def __str__(self) -> str:
        return f"{self.equipment.name} -> {self.user.name}"
