import json
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt

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
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.lower().startswith("token "):
        token = auth_header.split(" ", 1)[1]
    elif auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    elif "token" in request.GET:
        token = request.GET.get("token")
    if not token:
        return None
    return auth_service.login(token)


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


@csrf_exempt
def auth_login(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    data = _parse_body(request)
    token = data.get("token")
    if not token:
        return JsonResponse({"error": "token required"}, status=400)
    user = auth_service.login(token)
    if not user:
        return JsonResponse({"error": "invalid token"}, status=401)
    return JsonResponse(
        {
            "id": user.id,
            "name": user.name,
            "token": user.token,
            "role": user.role.name if user.role else None,
            "salary": float(user.salary),
            "phone": user.phone,
            "avatar_path": user.avatar_path,
        }
    )


@csrf_exempt
def auth_me(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    user = _user_from_request(request)
    if not user:
        return JsonResponse({"error": "unauthorized"}, status=401)
    return JsonResponse(
        {
            "id": user.id,
            "name": user.name,
            "token": user.token,
            "role": user.role.name if user.role else None,
            "salary": float(user.salary),
            "phone": user.phone,
            "avatar_path": user.avatar_path,
        }
    )


@csrf_exempt
def auth_profile(request):
    if request.method != "PUT":
        return HttpResponseNotAllowed(["PUT"])
    user = _user_from_request(request)
    if not user:
        return JsonResponse({"error": "unauthorized"}, status=401)
    data = _parse_body(request)
    allowed_fields = {"name", "phone", "avatar_path", "salary", "is_active"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if "salary" in update_data:
        update_data["salary"] = Decimal(str(update_data["salary"]))
    updated = auth_service.update_profile(user.id, update_data)
    return JsonResponse({"updated": updated})


@csrf_exempt
def customers(request):
    if request.method == "GET":
        items = [_customer_dict(c) for c in customer_service.get_all()]
        return JsonResponse(items, safe=False)
    if request.method == "POST":
        data = _parse_body(request)
        if not data.get("name") or not data.get("phone"):
            return JsonResponse({"error": "name and phone required"}, status=400)
        new_id = customer_service.create(
            {"name": data["name"], "phone": data["phone"], "email": data.get("email")}
        )
        return JsonResponse({"id": new_id}, status=201)
    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
def customer_detail(request, customer_id: int):
    if request.method == "GET":
        customer = customer_service.get_by_id(customer_id)
        if not customer:
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse(_customer_dict(customer))
    if request.method == "PUT":
        data = _parse_body(request)
        updated = customer_service.update(customer_id, data)
        if not updated:
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse({"updated": True})
    if request.method == "DELETE":
        deleted = customer_service.delete(customer_id)
        if not deleted:
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse({"deleted": True})
    return HttpResponseNotAllowed(["GET", "PUT", "DELETE"])


@csrf_exempt
def appointments(request):
    if request.method == "GET":
        items = [_appointment_dict(a) for a in appointment_service.get_all()]
        return JsonResponse(items, safe=False)
    if request.method == "POST":
        data = _parse_body(request)
        required_fields = ["customer_id", "date", "time", "service_type"]
        if not all(f in data for f in required_fields):
            return JsonResponse({"error": "missing fields"}, status=400)
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
        return JsonResponse({"id": appointment_id}, status=201)
    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
def appointments_by_date(request, dt: str):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    date = parse_date(dt)
    if not date:
        return JsonResponse({"error": "invalid date"}, status=400)
    items = [_appointment_dict(a) for a in appointment_service.get_by_date(date)]
    return JsonResponse(items, safe=False)


@csrf_exempt
def appointment_update(request, appointment_id: int):
    if request.method != "PUT":
        return HttpResponseNotAllowed(["PUT"])
    data = _parse_body(request)
    if "date" in data:
        data["date"] = parse_date(data["date"])
    updated = appointment_service.update(appointment_id, data)
    if not updated:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse({"updated": True})


@csrf_exempt
def orders(request):
    if request.method == "GET":
        items = [_order_dict(o) for o in order_service.get_all()]
        return JsonResponse(items, safe=False)
    if request.method == "POST":
        data = _parse_body(request)
        required = ["customer_name", "customer_phone", "total_amount", "paid_amount"]
        if not all(field in data for field in required):
            return JsonResponse({"error": "missing fields"}, status=400)
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
        return JsonResponse({"id": new_id}, status=201)
    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
def order_detail(request, order_id: int):
    if request.method == "GET":
        order = order_service.get_by_id(order_id)
        if not order:
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse(_order_dict(order))
    if request.method == "PUT":
        data = _parse_body(request)
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
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse({"updated": True})
    if request.method == "DELETE":
        deleted = order_service.delete(order_id)
        if not deleted:
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse({"deleted": True})
    return HttpResponseNotAllowed(["GET", "PUT", "DELETE"])


@csrf_exempt
def orders_by_staff(request, user_id: int):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    items = [_order_dict(o) for o in order_service.get_by_staff(user_id)]
    return JsonResponse(items, safe=False)


@csrf_exempt
def equipments(request):
    if request.method == "GET":
        items = [_equipment_dict(eq) for eq in equipment_service.get_all()]
        return JsonResponse(items, safe=False)
    if request.method == "POST":
        data = _parse_body(request)
        if "name" not in data or "count" not in data:
            return JsonResponse({"error": "name and count required"}, status=400)
        new_id = equipment_service.create({"name": data["name"], "count": data.get("count", 0)})
        return JsonResponse({"id": new_id}, status=201)
    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
def equipments_assigned(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
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
    return JsonResponse(items, safe=False)


@csrf_exempt
def expenses(request):
    if request.method == "GET":
        items = [_expense_dict(e) for e in expense_service.get_all()]
        return JsonResponse(items, safe=False)
    if request.method == "POST":
        data = _parse_body(request)
        if "amount" not in data or "date" not in data or "description" not in data:
            return JsonResponse({"error": "missing fields"}, status=400)
        expense_id = expense_service.create(
            {
                "amount": Decimal(str(data["amount"])),
                "date": parse_date(data["date"]),
                "description": data["description"],
            }
        )
        return JsonResponse({"id": expense_id}, status=201)
    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
def financial_stats(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    start = request.GET.get("start")
    end = request.GET.get("end")
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None
    stats = order_service.get_financial_stats(start_date, end_date)
    return JsonResponse(
        {
            "total_income": float(stats.total_income),
            "total_expense": float(stats.total_expense),
            "net": float(stats.net),
        }
    )
