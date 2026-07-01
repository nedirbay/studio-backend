"""API views for the management app.

Function-based DRF views returning plain JSON shaped exactly like the Flutter
`news_app` expects (see `news_app/lib/services/sync_service.dart` and
`lib/models/models.dart`). All endpoints require a valid JWT (the project-wide
default permission), the same token flow the app already uses for `/api/auth/*`.
"""

from decimal import Decimal, InvalidOperation

from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import (
    AppointmentService,
    AttendanceService,
    CustomerService,
    EquipmentService,
    ExpenseService,
    GalleryService,
    OrderService,
    OrderTypeService,
    ServiceCatalogService,
)
from .ws_utils import broadcast_order_event

customer_service = CustomerService()
appointment_service = AppointmentService()
order_service = OrderService()
equipment_service = EquipmentService()
expense_service = ExpenseService()
service_catalog = ServiceCatalogService()
order_type_service = OrderTypeService()
gallery_service = GalleryService()
attendance_service = AttendanceService()


# ---------------------------------------------------------------------------
# Serializers (plain dict builders)
# ---------------------------------------------------------------------------

def _customer_dict(c):
    return {
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "email": c.email,
        "created_at": c.created_at.isoformat(),
    }


def _appointment_dict(a):
    return {
        "id": a.id,
        "customer_id": a.customer_id,
        "customer_name": a.customer.name if a.customer else None,
        "customer_phone": a.customer.phone if a.customer else None,
        "date": a.date.isoformat(),
        "time": a.time,
        "service_type": a.service_type,
        "status": a.status,
        "notes": a.notes,
        "created_at": a.created_at.isoformat(),
    }


def _order_day_dict(day):
    return {
        "id": day.id,
        "date": day.date.isoformat(),
        "address": day.address,
        "daily_price": float(day.daily_price),
        "time": day.time,
        "equipments": [],
        "services": [
            {
                "id": s.id,
                "service_id": s.service_id,
                "service_name": s.service.name,
                "count": s.count,
            }
            for s in day.services.all()
        ],
    }


def _order_staff_dict(staff):
    return {
        "id": staff.id,
        "user_id": staff.user_id,
        "user_name": staff.user.username,
        "equipments": [
            {
                "id": e.id,
                "equipment_id": e.equipment_id,
                "equipment_name": e.equipment.name,
                "count": e.count,
                "received_at": e.received_at.isoformat() if e.received_at else None,
                "returned_at": e.returned_at.isoformat() if e.returned_at else None,
            }
            for e in staff.equipments.all()
        ],
    }


def _order_dict(order):
    return {
        "id": order.id,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "total_amount": float(order.total_amount),
        "paid_amount": float(order.paid_amount),
        "remaining_amount": float(order.remaining_amount),
        "order_type_id": order.order_type_id,
        "created_at": order.created_at.isoformat(),
        "status": order.status,
        "days": [_order_day_dict(d) for d in order.days.all()],
        "staff": [_order_staff_dict(s) for s in order.staff.all()],
    }


def _equipment_dict(eq):
    return {"id": eq.id, "name": eq.name, "count": eq.count}


def _expense_dict(e):
    return {
        "id": e.id,
        "amount": float(e.amount),
        "date": e.date.isoformat(),
        "description": e.description,
        "created_at": e.created_at.isoformat(),
    }


def _gallery_dict(g):
    return {
        "id": g.id,
        "title": g.title,
        "description": g.description,
        "image_path": g.image_path,
        "category": g.category,
        "created_at": g.created_at.isoformat(),
    }


def _attendance_dict(a):
    return {
        "id": a.id,
        "order_id": a.order_id,
        "user_id": a.user_id,
        "user_name": a.user.username,
        "date": a.date.isoformat(),
        "arrived_at": a.arrived_at.isoformat() if a.arrived_at else None,
    }


def _to_decimal(value, default="0"):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _build_order_payload(data):
    """Parse a create/update order request body into service-layer dicts."""
    order_data = {
        "customer_name": data.get("customer_name", ""),
        "customer_phone": data.get("customer_phone", ""),
        "total_amount": _to_decimal(data.get("total_amount", 0)),
        "paid_amount": _to_decimal(data.get("paid_amount", 0)),
        "order_type_id": data.get("order_type_id"),
        "status": data.get("status", "pending"),
    }
    days_data = []
    for day in data.get("days", []):
        if "date" not in day or "address" not in day or "daily_price" not in day:
            continue
        days_data.append(
            {
                "date": parse_date(day["date"]),
                "address": day["address"],
                "daily_price": _to_decimal(day["daily_price"]),
                "time": day.get("time"),
                "equipments": [],
                "services": [
                    {"service_id": s["service_id"], "count": s.get("count", 1)}
                    for s in day.get("services", [])
                    if "service_id" in s
                ],
            }
        )
    staff_data = []
    for st in data.get("staff", []):
        if "user_id" not in st:
            continue
        staff_data.append(
            {
                "user_id": st["user_id"],
                "equipments": [
                    {"equipment_id": e["equipment_id"], "count": e.get("count", 1)}
                    for e in st.get("equipments", [])
                    if "equipment_id" in e
                ],
            }
        )
    return order_data, days_data, staff_data


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def customers(request):
    if request.method == "GET":
        return Response([_customer_dict(c) for c in customer_service.get_all()])
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
        if not customer_service.update(customer_id, request.data):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"updated": True})
    if not customer_service.delete(customer_id):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def appointments(request):
    if request.method == "GET":
        return Response([_appointment_dict(a) for a in appointment_service.get_all()])
    data = request.data
    required = ["customer_id", "date", "time", "service_type"]
    if not all(f in data for f in required):
        return Response({"error": "missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    new_id = appointment_service.create(
        {
            "customer_id": data["customer_id"],
            "date": parse_date(data["date"]),
            "time": data["time"],
            "service_type": data["service_type"],
            "status": data.get("status", "garaşylýar"),
            "notes": data.get("notes"),
        }
    )
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def appointments_by_date(request, dt: str):
    date = parse_date(dt)
    if not date:
        return Response({"error": "invalid date"}, status=status.HTTP_400_BAD_REQUEST)
    return Response([_appointment_dict(a) for a in appointment_service.get_by_date(date)])


@api_view(["PUT", "DELETE"])
def appointment_detail(request, appointment_id: int):
    if request.method == "DELETE":
        if not appointment_service.delete(appointment_id):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"deleted": True})
    data = dict(request.data)
    if "date" in data:
        data["date"] = parse_date(data["date"])
    if not appointment_service.update(appointment_id, data):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"updated": True})


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def orders(request):
    if request.method == "GET":
        orders_qs = order_service.get_all()
        # Admins and staff see all orders, regular users see only their own
        if not (request.user.is_superuser or (request.user.role and request.user.role.name == "Admin")):
            orders_qs = [o for o in orders_qs if o.user_id == request.user.id]
        return Response([_order_dict(o) for o in orders_qs])
    data = request.data
    required = ["customer_name", "customer_phone", "total_amount", "paid_amount"]
    if not all(f in data for f in required):
        return Response({"error": "missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    order_data, days_data, staff_data = _build_order_payload(data)
    if request.user.is_authenticated:
        order_data["user"] = request.user
    new_id = order_service.create(order_data, days_data, staff_data)
    o = order_service.get_by_id(new_id)
    if o:
        broadcast_order_event("order_created", {"order": _order_dict(o)})
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE", "PATCH"])
def order_detail(request, order_id: int):
    order = order_service.get_by_id(order_id)
    if not order:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions: Admin/staff can access any order, regular users only their own
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == "Admin")):
        if order.user_id != request.user.id:
            return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        return Response(_order_dict(order))
    if request.method == "PUT":
        order_data, days_data, staff_data = _build_order_payload(request.data)
        if not order_service.update(order_id, order_data, days_data, staff_data):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        o = order_service.get_by_id(order_id)
        if o:
            broadcast_order_event("order_updated", {"order": _order_dict(o)})
        return Response({"updated": True})
    if request.method == "PATCH":
        status_val = request.data.get("status")
        if not status_val:
            return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = status_val
        order.save()
        broadcast_order_event("order_updated", {"order": _order_dict(order)})
        return Response(_order_dict(order))
    # For delete, we must broadcast before deleting
    broadcast_order_event("order_deleted", {"order_id": order_id})
    if not order_service.delete(order_id):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


@api_view(["GET"])
def orders_by_staff(request, user_id: int):
    return Response([_order_dict(o) for o in order_service.get_by_staff(user_id)])


# ---------------------------------------------------------------------------
# Equipments
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def equipments(request):
    if request.method == "GET":
        return Response([_equipment_dict(e) for e in equipment_service.get_all()])
    data = request.data
    if "name" not in data:
        return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)
    new_id = equipment_service.create({"name": data["name"], "count": data.get("count", 0)})
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
def equipment_detail(request, equipment_id: int):
    if request.method == "DELETE":
        if not equipment_service.delete(equipment_id):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"deleted": True})
    if not equipment_service.update(equipment_id, request.data):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"updated": True})


@api_view(["GET"])
def equipments_assigned(request):
    return Response(
        [
            {
                "id": a.id,
                "equipment_id": a.equipment_id,
                "equipment_name": a.equipment.name,
                "user_id": a.user_id,
                "user_name": a.user.username,
                "count": a.count,
                "assigned_at": a.assigned_at.isoformat(),
            }
            for a in equipment_service.get_assigned()
        ]
    )


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def expenses(request):
    if request.method == "GET":
        return Response([_expense_dict(e) for e in expense_service.get_all()])
    data = request.data
    if "amount" not in data or "date" not in data:
        return Response({"error": "amount and date required"}, status=status.HTTP_400_BAD_REQUEST)
    new_id = expense_service.create(
        {
            "amount": _to_decimal(data["amount"]),
            "date": parse_date(data["date"]),
            "description": data.get("description", ""),
        }
    )
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
def expense_detail(request, expense_id: int):
    if request.method == "DELETE":
        if not expense_service.delete(expense_id):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"deleted": True})
    data = dict(request.data)
    if "amount" in data:
        data["amount"] = _to_decimal(data["amount"])
    if "date" in data:
        data["date"] = parse_date(data["date"])
    if not expense_service.update(expense_id, data):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"updated": True})


# ---------------------------------------------------------------------------
# Services & Order types (simple named lists)
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def services(request):
    if request.method == "GET":
        return Response([{"id": s.id, "name": s.name} for s in service_catalog.get_all()])
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
    if not request.data.get("name"):
        return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"id": service_catalog.create(request.data["name"])}, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
def service_detail(request, service_id: int):
    if request.method == "DELETE":
        if not service_catalog.delete(service_id):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"deleted": True})
    if not request.data.get("name"):
        return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)
    if not service_catalog.update(service_id, request.data["name"]):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"updated": True})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def order_types(request):
    if request.method == "GET":
        return Response([{"id": t.id, "name": t.name} for t in order_type_service.get_all()])
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
    if not request.data.get("name"):
        return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"id": order_type_service.create(request.data["name"])}, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
def order_type_detail(request, order_type_id: int):
    if request.method == "DELETE":
        if not order_type_service.delete(order_type_id):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"deleted": True})
    if not request.data.get("name"):
        return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)
    if not order_type_service.update(order_type_id, request.data["name"]):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"updated": True})


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def gallery(request):
    if request.method == "GET":
        return Response([_gallery_dict(g) for g in gallery_service.get_all()])
    data = request.data
    if not data.get("title") or not data.get("image_path") or not data.get("category"):
        return Response(
            {"error": "title, image_path and category required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    new_id = gallery_service.create(
        {
            "title": data["title"],
            "description": data.get("description"),
            "image_path": data["image_path"],
            "category": data["category"],
        }
    )
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def gallery_detail(request, item_id: int):
    if request.method == "GET":
        item = gallery_service.get_by_id(item_id)
        if not item:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_gallery_dict(item))
    if request.method == "PUT":
        if not gallery_service.update(item_id, request.data):
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"updated": True})
    if not gallery_service.delete(item_id):
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


# ---------------------------------------------------------------------------
# Attendance & stats
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def attendance(request):
    if request.method == "GET":
        order_id = request.GET.get("order_id")
        user_id = request.GET.get("user_id")
        items = attendance_service.get_all(
            order_id=int(order_id) if order_id else None,
            user_id=int(user_id) if user_id else None,
        )
        return Response([_attendance_dict(a) for a in items])
    data = request.data
    if "order_id" not in data or "user_id" not in data or "date" not in data:
        return Response(
            {"error": "order_id, user_id and date required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    new_id = attendance_service.create(
        {
            "order_id": data["order_id"],
            "user_id": data["user_id"],
            "date": parse_date(data["date"]),
            "arrived_at": data.get("arrived_at"),
        }
    )
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def financial_stats(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    stats = order_service.get_financial_stats(
        parse_date(start) if start else None,
        parse_date(end) if end else None,
    )
    return Response(
        {
            "total_income": float(stats.total_income),
            "total_expense": float(stats.total_expense),
            "net": float(stats.net),
        }
    )
