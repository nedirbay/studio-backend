from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db.models import Sum

from .models import (
    Appointment,
    Customer,
    Equipment,
    EquipmentAssignment,
    Expense,
    Order,
    OrderDay,
    OrderStaff,
)


@dataclass
class FinancialStats:
    total_income: Decimal
    total_expense: Decimal
    net: Decimal


class CustomerService:
    def get_all(self):
        return list(Customer.objects.all().order_by("-created_at"))

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return Customer.objects.filter(id=customer_id).first()

    def create(self, data: dict) -> int:
        customer = Customer.objects.create(**data)
        return customer.id

    def update(self, customer_id: int, data: dict) -> bool:
        updated = Customer.objects.filter(id=customer_id).update(**data)
        return updated > 0

    def delete(self, customer_id: int) -> bool:
        deleted, _ = Customer.objects.filter(id=customer_id).delete()
        return deleted > 0


class AppointmentService:
    def get_all(self):
        return list(Appointment.objects.select_related("customer").order_by("-date", "-time"))

    def get_by_date(self, date):
        return list(
            Appointment.objects.filter(date=date).select_related("customer").order_by("-time")
        )

    def create(self, data: dict) -> int:
        appointment = Appointment.objects.create(**data)
        return appointment.id

    def update(self, appointment_id: int, data: dict) -> bool:
        updated = Appointment.objects.filter(id=appointment_id).update(**data)
        return updated > 0


class OrderService:
    def get_all(self):
        return list(Order.objects.all().order_by("-created_at"))

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return (
            Order.objects.filter(id=order_id)
            .prefetch_related("days", "staff__user")
            .first()
        )

    def create(self, order_data: dict, days_data: list, staff_data: list) -> int:
        order = Order.objects.create(**order_data)
        for day in days_data:
            OrderDay.objects.create(order=order, **day)
        for staff in staff_data:
            OrderStaff.objects.create(order=order, **staff)
        return order.id

    def update(self, order_id: int, order_data: dict, days_data: list, staff_data: list) -> bool:
        if not Order.objects.filter(id=order_id).exists():
            return False
        Order.objects.filter(id=order_id).update(**order_data)
        OrderDay.objects.filter(order_id=order_id).delete()
        for day in days_data:
            OrderDay.objects.create(order_id=order_id, **day)
        OrderStaff.objects.filter(order_id=order_id).delete()
        for staff in staff_data:
            OrderStaff.objects.create(order_id=order_id, **staff)
        return True

    def delete(self, order_id: int) -> bool:
        deleted, _ = Order.objects.filter(id=order_id).delete()
        return deleted > 0

    def get_by_staff(self, user_id: int):
        orders = (
            Order.objects.filter(staff__user_id=user_id)
            .distinct()
            .prefetch_related("days", "staff__user")
            .order_by("-created_at")
        )
        return list(orders)

    def get_financial_stats(self, start=None, end=None) -> FinancialStats:
        orders = Order.objects.all()
        expenses = Expense.objects.all()

        if start:
            orders = orders.filter(created_at__date__gte=start)
            expenses = expenses.filter(date__gte=start)
        if end:
            orders = orders.filter(created_at__date__lte=end)
            expenses = expenses.filter(date__lte=end)

        total_income = orders.aggregate(total=Sum("paid_amount"))["total"] or Decimal(0)
        total_expense = expenses.aggregate(total=Sum("amount"))["total"] or Decimal(0)
        net = total_income - total_expense
        return FinancialStats(total_income=total_income, total_expense=total_expense, net=net)


class EquipmentService:
    def get_all(self):
        return list(Equipment.objects.all())

    def create(self, data: dict) -> int:
        equipment = Equipment.objects.create(**data)
        return equipment.id

    def get_assigned(self):
        assignments = (
            EquipmentAssignment.objects.select_related("equipment", "user")
            .all()
            .order_by("equipment__name")
        )
        return assignments


class ExpenseService:
    def get_all(self):
        return list(Expense.objects.all().order_by("-date"))

    def create(self, data: dict) -> int:
        expense = Expense.objects.create(**data)
        return expense.id
