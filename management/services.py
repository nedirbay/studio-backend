"""Service layer for the management app.

Encapsulates all data-access / business logic so the views stay thin. Mirrors
the operations the Flutter `news_app` performs locally (create/update/delete +
sync reads) and adds server-side financial stats.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import Sum

from .models import (
    Appointment,
    Customer,
    Equipment,
    EquipmentAssignment,
    Expense,
    GalleryItem,
    Order,
    OrderDay,
    OrderDayService,
    OrderStaff,
    OrderStaffEquipment,
    OrderType,
    Service,
    StaffAttendance,
)


@dataclass
class FinancialStats:
    total_income: Decimal
    total_expense: Decimal
    net: Decimal


class CustomerService:
    def get_all(self):
        return list(Customer.objects.all())

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return Customer.objects.filter(id=customer_id).first()

    def create(self, data: dict) -> int:
        return Customer.objects.create(**data).id

    def update(self, customer_id: int, data: dict) -> bool:
        allowed = {k: data[k] for k in ("name", "phone", "email") if k in data}
        return Customer.objects.filter(id=customer_id).update(**allowed) > 0

    def delete(self, customer_id: int) -> bool:
        deleted, _ = Customer.objects.filter(id=customer_id).delete()
        return deleted > 0


class AppointmentService:
    def get_all(self):
        return list(Appointment.objects.select_related("customer"))

    def get_by_date(self, date):
        return list(
            Appointment.objects.filter(date=date)
            .select_related("customer")
            .order_by("-time")
        )

    def create(self, data: dict) -> int:
        return Appointment.objects.create(**data).id

    def update(self, appointment_id: int, data: dict) -> bool:
        allowed = {
            k: data[k]
            for k in ("customer_id", "date", "time", "service_type", "status", "notes")
            if k in data
        }
        return Appointment.objects.filter(id=appointment_id).update(**allowed) > 0

    def delete(self, appointment_id: int) -> bool:
        deleted, _ = Appointment.objects.filter(id=appointment_id).delete()
        return deleted > 0


class OrderService:
    def _base_qs(self):
        return Order.objects.prefetch_related(
            "days__services__service",
            "staff__user",
            "staff__equipments__equipment",
        )

    def get_all(self):
        return list(self._base_qs())

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self._base_qs().filter(id=order_id).first()

    def get_by_staff(self, user_id: int):
        return list(self._base_qs().filter(staff__user_id=user_id).distinct())

    @transaction.atomic
    def create(self, order_data: dict, days_data: list, staff_data: list) -> int:
        order = Order.objects.create(**order_data)
        self._sync_days(order, days_data)
        self._sync_staff(order, staff_data)
        return order.id

    @transaction.atomic
    def update(self, order_id: int, order_data: dict, days_data: list, staff_data: list) -> bool:
        if not Order.objects.filter(id=order_id).exists():
            return False
        Order.objects.filter(id=order_id).update(**order_data)
        order = Order.objects.get(id=order_id)
        order.days.all().delete()
        order.staff.all().delete()
        self._sync_days(order, days_data)
        self._sync_staff(order, staff_data)
        return True

    def delete(self, order_id: int) -> bool:
        deleted, _ = Order.objects.filter(id=order_id).delete()
        return deleted > 0

    def _sync_days(self, order: Order, days_data: list):
        for day in days_data:
            day.pop("equipments", None)
            services = day.pop("services", [])
            order_day = OrderDay.objects.create(order=order, **day)
            for sv in services:
                OrderDayService.objects.create(
                    order_day=order_day,
                    service_id=sv["service_id"],
                    count=sv.get("count", 1),
                )

    def _sync_staff(self, order: Order, staff_data: list):
        for st in staff_data:
            equipments = st.pop("equipments", [])
            order_staff = OrderStaff.objects.create(order=order, user_id=st["user_id"])
            for eq in equipments:
                OrderStaffEquipment.objects.create(
                    order_staff=order_staff,
                    equipment_id=eq["equipment_id"],
                    count=eq.get("count", 1),
                )

    def get_financial_stats(self, start=None, end=None) -> FinancialStats:
        orders = Order.objects.all()
        expenses = Expense.objects.all()
        if start:
            orders = orders.filter(created_at__date__gte=start)
            expenses = expenses.filter(date__gte=start)
        if end:
            orders = orders.filter(created_at__date__lte=end)
            expenses = expenses.filter(date__lte=end)
        total_income = orders.aggregate(t=Sum("paid_amount"))["t"] or Decimal(0)
        total_expense = expenses.aggregate(t=Sum("amount"))["t"] or Decimal(0)
        return FinancialStats(
            total_income=total_income,
            total_expense=total_expense,
            net=total_income - total_expense,
        )


class EquipmentService:
    def get_all(self):
        return list(Equipment.objects.all())

    def create(self, data: dict) -> int:
        return Equipment.objects.create(**data).id

    def update(self, equipment_id: int, data: dict) -> bool:
        allowed = {k: data[k] for k in ("name", "count") if k in data}
        return Equipment.objects.filter(id=equipment_id).update(**allowed) > 0

    def delete(self, equipment_id: int) -> bool:
        deleted, _ = Equipment.objects.filter(id=equipment_id).delete()
        return deleted > 0

    def get_assigned(self):
        return list(
            EquipmentAssignment.objects.select_related("equipment", "user").order_by(
                "equipment__name"
            )
        )


class ExpenseService:
    def get_all(self):
        return list(Expense.objects.all())

    def create(self, data: dict) -> int:
        return Expense.objects.create(**data).id

    def update(self, expense_id: int, data: dict) -> bool:
        allowed = {k: data[k] for k in ("amount", "date", "description") if k in data}
        return Expense.objects.filter(id=expense_id).update(**allowed) > 0

    def delete(self, expense_id: int) -> bool:
        deleted, _ = Expense.objects.filter(id=expense_id).delete()
        return deleted > 0


class _SimpleNamedService:
    """Shared CRUD for the trivial `{id, name}` resources (Service, OrderType)."""

    model = None

    def get_all(self):
        return list(self.model.objects.all())

    def create(self, name: str) -> int:
        return self.model.objects.create(name=name).id

    def update(self, obj_id: int, name: str) -> bool:
        return self.model.objects.filter(id=obj_id).update(name=name) > 0

    def delete(self, obj_id: int) -> bool:
        deleted, _ = self.model.objects.filter(id=obj_id).delete()
        return deleted > 0


class ServiceCatalogService(_SimpleNamedService):
    model = Service


class OrderTypeService(_SimpleNamedService):
    model = OrderType


class GalleryService:
    def get_all(self):
        return list(GalleryItem.objects.all())

    def get_by_id(self, item_id: int) -> Optional[GalleryItem]:
        return GalleryItem.objects.filter(id=item_id).first()

    def create(self, data: dict) -> int:
        return GalleryItem.objects.create(**data).id

    def update(self, item_id: int, data: dict) -> bool:
        allowed = {
            k: data[k]
            for k in ("title", "description", "image_path", "category")
            if k in data
        }
        return GalleryItem.objects.filter(id=item_id).update(**allowed) > 0

    def delete(self, item_id: int) -> bool:
        deleted, _ = GalleryItem.objects.filter(id=item_id).delete()
        return deleted > 0


class AttendanceService:
    def get_all(self, order_id=None, user_id=None):
        qs = StaffAttendance.objects.select_related("user")
        if order_id is not None:
            qs = qs.filter(order_id=order_id)
        if user_id is not None:
            qs = qs.filter(user_id=user_id)
        return list(qs)

    def create(self, data: dict) -> int:
        return StaffAttendance.objects.create(**data).id
