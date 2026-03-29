import json
from datetime import datetime, timedelta
from decimal import Decimal

import jwt
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Appointment, Customer, Equipment, Expense, Order, OrderDay, OrderStaff, User
from .services import (
    AppointmentService,
    AuthService,
    CustomerService,
    EquipmentService,
    ExpenseService,
    OrderService,
)

auth_service = AuthService()
customer_service = CustomerService()
appointment_service = AppointmentService()
order_service = OrderService()
equipment_service = EquipmentService()
expense_service = ExpenseService()


def _parse_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _user_from_request(request):
    if hasattr(request, "user") and getattr(request, "user").is_authenticated:
        return request.user
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    elif auth_header.lower().startswith("token "):
        token = auth_header.split(" ", 1)[1]
    elif "token" in request.GET:
        token = request.GET.get("token")
    if not token:
        return None
    # Try JWT first
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id:
            return User.objects.filter(id=user_id, is_active=True).select_related("role").first()
    except jwt.PyJWTError:
        pass
    # fallback to legacy token auth
    return auth_service.login(token)


def _issue_jwt(user: User, minutes: int = 30, token_type: str = "access"):
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    payload = {
        "type": token_type,
        "user_id": user.id,
        "role": user.role.name if user.role else None,
        "exp": exp,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def _issue_refresh_jwt(user: User, days: int = 7):
    return _issue_jwt(user, minutes=days * 24 * 60, token_type="refresh")


def _customer_dict(customer: Customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "created_at": customer.created_at.isoformat(),
    }


def _appointment_dict(appointment: Appointment):
    return {
        "id": appointment.id,
        "customer_id": appointment.customer_id,
        "customer_name": appointment.customer.name if appointment.customer else None,
        "date": appointment.date.isoformat(),
        "time": appointment.time,
        "service_type": appointment.service_type,
        "status": appointment.status,
        "notes": appointment.notes,
        "created_at": appointment.created_at.isoformat(),
    }


def _order_day_dict(day: OrderDay):
    return {
        "id": day.id,
        "date": day.date.isoformat(),
        "address": day.address,
        "daily_price": float(day.daily_price),
        "time": day.time,
    }


def _order_staff_dict(staff: OrderStaff):
    return {
        "id": staff.id,
        "user_id": staff.user_id,
        "user_name": staff.user.name,
        "role": staff.role,
    }


def _order_dict(order: Order):
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "total_amount": float(order.total_amount),
        "paid_amount": float(order.paid_amount),
        "remaining_amount": float(order.remaining_amount),
        "order_type_id": order.order_type_id,
        "created_at": order.created_at.isoformat(),
        "days": [_order_day_dict(day) for day in order.days.all()],
        "staff": [_order_staff_dict(st) for st in order.staff.all()],
    }


def _equipment_dict(eq: Equipment):
    return {"id": eq.id, "name": eq.name, "count": eq.count}


def _expense_dict(exp: Expense):
    return {
        "id": exp.id,
        "amount": float(exp.amount),
        "date": exp.date.isoformat(),
        "description": exp.description,
        "created_at": exp.created_at.isoformat(),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    data = request.data
    token = data.get("token")
    if not token:
        return Response({"error": "token required"}, status=status.HTTP_400_BAD_REQUEST)
    user = auth_service.login(token)
    if not user:
        return Response({"error": "invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    jwt_token = _issue_jwt(user)
    refresh = _issue_refresh_jwt(user)
    return Response(
        {
            "id": user.id,
            "name": user.name,
            "role": user.role.name if user.role else None,
            "salary": float(user.salary),
            "phone": user.phone,
            "avatar_path": user.avatar_path,
            "jwt": jwt_token,
            "refresh": refresh,
        }
    )


@api_view(["GET"])
def auth_me(request):
    user = _user_from_request(request)
    if not user:
        return Response({"error": "unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(
        {
            "id": user.id,
            "name": user.name,
            "role": user.role.name if user.role else None,
            "salary": float(user.salary),
            "phone": user.phone,
            "avatar_path": user.avatar_path,
        }
    )


@api_view(["PUT"])
def auth_profile(request):
    user = _user_from_request(request)
    if not user:
        return Response({"error": "unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    data = request.data
    allowed_fields = {"name", "phone", "avatar_path", "salary", "is_active"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if "salary" in update_data:
        update_data["salary"] = Decimal(str(update_data["salary"]))
    updated = auth_service.update_profile(user.id, update_data)
    return Response({"updated": updated})


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_refresh(request):
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return Response({"error": "invalid token type"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id=payload.get("user_id"), is_active=True).first()
        if not user:
            return Response({"error": "user not found"}, status=status.HTTP_401_UNAUTHORIZED)
        new_access = _issue_jwt(user)
        new_refresh = _issue_refresh_jwt(user)
        return Response({"jwt": new_access, "refresh": new_refresh})
    except jwt.ExpiredSignatureError:
        return Response({"error": "refresh expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.PyJWTError:
        return Response({"error": "invalid token"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
def customers(request):
    if request.method == "GET":
        items = [_customer_dict(c) for c in customer_service.get_all()]
        return Response(items)
    data = request.data
    if not data.get("name") or not data.get("phone"):
        return Response({"error": "name and phone required"}, status=status.HTTP_400_BAD_REQUEST)
    new_id = customer_service.create(
        {"name": data["name"], "phone": data["phone"], "email": data.get("email")}
    )
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def customer_detail(request, customer_id: int):
    if request.method == "GET":
        customer = customer_service.get_by_id(customer_id)
        if not customer:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_customer_dict(customer))
    if request.method == "PUT":
        data = request.data
        updated = customer_service.update(customer_id, data)
        if not updated:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"updated": True})
    deleted = customer_service.delete(customer_id)
    if not deleted:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


@api_view(["GET", "POST"])
def appointments(request):
    if request.method == "GET":
        items = [_appointment_dict(a) for a in appointment_service.get_all()]
        return Response(items)
    data = request.data
    required_fields = ["customer_id", "date", "time", "service_type"]
    if not all(f in data for f in required_fields):
        return Response({"error": "missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    appointment_id = appointment_service.create(
        {
            "customer_id": data["customer_id"],
            "date": parse_date(data["date"]),
            "time": data["time"],
            "service_type": data["service_type"],
            "status": data.get("status", "garaşylýar"),
            "notes": data.get("notes"),
        }
    )
    return Response({"id": appointment_id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def appointments_by_date(request, dt: str):
    date = parse_date(dt)
    if not date:
        return Response({"error": "invalid date"}, status=status.HTTP_400_BAD_REQUEST)
    items = [_appointment_dict(a) for a in appointment_service.get_by_date(date)]
    return Response(items)


@api_view(["PUT"])
def appointment_update(request, appointment_id: int):
    data = request.data
    if "date" in data:
        data["date"] = parse_date(data["date"])
    updated = appointment_service.update(appointment_id, data)
    if not updated:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"updated": True})


@api_view(["GET", "POST"])
def orders(request):
    if request.method == "GET":
        items = [_order_dict(o) for o in order_service.get_all()]
        return Response(items)
    data = request.data
    required = ["customer_name", "customer_phone", "total_amount", "paid_amount"]
    if not all(field in data for field in required):
        return Response({"error": "missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    order_data = {
        "customer_name": data["customer_name"],
        "customer_phone": data["customer_phone"],
        "total_amount": Decimal(str(data["total_amount"])),
        "paid_amount": Decimal(str(data["paid_amount"])),
        "order_type_id": data.get("order_type_id"),
    }
    days_data = []
    for day in data.get("days", []):
        if "date" not in day or "address" not in day or "daily_price" not in day:
            continue
        days_data.append(
            {
                "date": parse_date(day["date"]),
                "address": day["address"],
                "daily_price": Decimal(str(day["daily_price"])),
                "time": day.get("time"),
            }
        )
    staff_data = []
    for st in data.get("staff", []):
        if "user_id" not in st:
            continue
        staff_data.append({"user_id": st["user_id"], "role": st.get("role")})
    new_id = order_service.create(order_data, days_data, staff_data)
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def order_detail(request, order_id: int):
    if request.method == "GET":
        order = order_service.get_by_id(order_id)
        if not order:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_order_dict(order))
    if request.method == "PUT":
        data = request.data
        order_data = {
            "customer_name": data.get("customer_name", ""),
            "customer_phone": data.get("customer_phone", ""),
            "total_amount": Decimal(str(data.get("total_amount", 0))),
            "paid_amount": Decimal(str(data.get("paid_amount", 0))),
            "order_type_id": data.get("order_type_id"),
        }
        days_data = []
        for day in data.get("days", []):
            if "date" not in day or "address" not in day or "daily_price" not in day:
                continue
            days_data.append(
                {
                    "date": parse_date(day["date"]),
                    "address": day["address"],
                    "daily_price": Decimal(str(day["daily_price"])),
                    "time": day.get("time"),
                }
            )
        staff_data = []
        for st in data.get("staff", []):
            if "user_id" not in st:
                continue
            staff_data.append({"user_id": st["user_id"], "role": st.get("role")})
        updated = order_service.update(order_id, order_data, days_data, staff_data)
        if not updated:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"updated": True})
    deleted = order_service.delete(order_id)
    if not deleted:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


@api_view(["GET"])
def orders_by_staff(request, user_id: int):
    items = [_order_dict(o) for o in order_service.get_by_staff(user_id)]
    return Response(items)


@api_view(["GET", "POST"])
def equipments(request):
    if request.method == "GET":
        items = [_equipment_dict(eq) for eq in equipment_service.get_all()]
        return Response(items)
    data = request.data
    if "name" not in data or "count" not in data:
        return Response({"error": "name and count required"}, status=status.HTTP_400_BAD_REQUEST)
    new_id = equipment_service.create({"name": data["name"], "count": data.get("count", 0)})
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def equipments_assigned(request):
    items = [
        {
            "id": assign.id,
            "equipment_id": assign.equipment_id,
            "equipment_name": assign.equipment.name,
            "user_id": assign.user_id,
            "user_name": assign.user.name,
            "count": assign.count,
            "assigned_at": assign.assigned_at.isoformat(),
        }
        for assign in equipment_service.get_assigned()
    ]
    return Response(items)


@api_view(["GET", "POST"])
def expenses(request):
    if request.method == "GET":
        items = [_expense_dict(e) for e in expense_service.get_all()]
        return Response(items)
    data = request.data
    if "amount" not in data or "date" not in data or "description" not in data:
        return Response({"error": "missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    expense_id = expense_service.create(
        {
            "amount": Decimal(str(data["amount"])),
            "date": parse_date(data["date"]),
            "description": data["description"],
        }
    )
    return Response({"id": expense_id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def financial_stats(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None
    stats = order_service.get_financial_stats(start_date, end_date)
    return Response(
        {
            "total_income": float(stats.total_income),
            "total_expense": float(stats.total_expense),
            "net": float(stats.net),
        }
    )
