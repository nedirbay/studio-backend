from decimal import Decimal

from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Appointment, Customer, Equipment, Expense, Order, OrderDay, OrderStaff, Banner, Promo, OrderType, MobileAppVersion, Currency
from .services import AppointmentService, CustomerService, EquipmentService, ExpenseService, OrderService

customer_service = CustomerService()
appointment_service = AppointmentService()
order_service = OrderService()
equipment_service = EquipmentService()
expense_service = ExpenseService()


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
        "user_name": staff.user.username,
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


def _banner_dict(banner: Banner):
    return {
        "id": banner.id,
        "title": banner.title,
        "subtitle": banner.subtitle,
        "description": banner.description,
        "image": banner.image_url,
        "ctaText": banner.cta_text,
        "bgColor": banner.bg_color,
        "product_id": banner.product_id,
    }


def _promo_dict(promo: Promo):
    return {
        "id": promo.id,
        "title": promo.title,
        "subtitle": promo.subtitle,
        "badge": promo.badge,
        "image": promo.image_url,
        "link": promo.link_url,
        "bgGradient": promo.bg_gradient,
    }


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
@permission_classes([AllowAny])
def orders(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
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
    o = order_service.get_by_id(new_id)
    if o:
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("main_order_created", {"order": _order_dict(o)})
        except Exception as e:
            print("Failed to broadcast main_order_created:", e)
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
        o = order_service.get_by_id(order_id)
        if o:
            try:
                from management.ws_utils import broadcast_order_event
                broadcast_order_event("main_order_updated", {"order": _order_dict(o)})
            except Exception as e:
                print("Failed to broadcast main_order_updated:", e)
        return Response({"updated": True})
    try:
        from management.ws_utils import broadcast_order_event
        broadcast_order_event("main_order_deleted", {"order_id": order_id})
    except Exception as e:
        print("Failed to broadcast main_order_deleted:", e)
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
            "user_name": assign.user.username,
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
    
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def order_types(request):
    if request.method == "GET":
        items = [{"id": ot.id, "name": ot.name} for ot in OrderType.objects.all()]
        return Response(items)
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
    data = request.data
    if "name" not in data:
        return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)
    ot = OrderType.objects.create(name=data["name"])
    return Response({"id": ot.id}, status=status.HTTP_201_CREATED)


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


@api_view(["GET", "POST", "PUT", "DELETE"])
@permission_classes([AllowAny])
def banners(request):
    if request.method == "GET":
        return Response([_banner_dict(b) for b in Banner.objects.all()])
    
    # Simple CRUD logic for admin
    if request.method == "POST":
        data = request.data
        banner = Banner.objects.create(
            title=data.get("title", ""),
            subtitle=data.get("subtitle"),
            description=data.get("description"),
            image_url=data.get("image", ""),
            cta_text=data.get("ctaText", "Söwda et"),
            bg_color=data.get("bgColor", "from-red-900/80"),
            product_id=data.get("product_id")
        )
        return Response(_banner_dict(banner), status=status.HTTP_201_CREATED)
    
    if request.method == "PUT":
        data = request.data
        banner_id = data.get("id")
        if not banner_id:
            return Response({"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST)
        
        banner = Banner.objects.filter(id=banner_id).first()
        if not banner:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        
        banner.title = data.get("title", banner.title)
        banner.subtitle = data.get("subtitle", banner.subtitle)
        banner.description = data.get("description", banner.description)
        banner.image_url = data.get("image", banner.image_url)
        banner.cta_text = data.get("ctaText", banner.cta_text)
        banner.bg_color = data.get("bgColor", banner.bg_color)
        banner.product_id = data.get("product_id", banner.product_id)
        banner.save()
        return Response(_banner_dict(banner))

    if request.method == "DELETE":
        banner_id = request.data.get("id") or request.GET.get("id")
        if not banner_id:
            return Response({"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST)
        
        Banner.objects.filter(id=banner_id).delete()
        return Response({"deleted": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def promos(request):
    return Response([_promo_dict(p) for p in Promo.objects.all()])


def _mobile_app_version_dict(request, version):
    return {
        "id": version.id,
        "version_name": version.version_name,
        "version_code": version.version_code,
        "file_url": request.build_absolute_uri(version.file.url) if version.file else None,
        "is_active": version.is_active,
        "description": version.description,
        "created_at": version.created_at.isoformat(),
        "updated_at": version.updated_at.isoformat(),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def active_mobile_app(request):
    """Get the currently active mobile app version details."""
    active_version = MobileAppVersion.objects.filter(is_active=True).first()
    if not active_version:
        return Response(None)
    return Response(_mobile_app_version_dict(request, active_version))


@api_view(["GET", "POST"])
def mobile_app_versions(request):
    """
    Admin-only endpoints:
    GET: List all uploaded versions.
    POST: Upload a new version (APK file, version name, version code, description, active flag).
    """
    # Admin Permission Check
    if not (request.user.is_authenticated and (request.user.is_superuser or (request.user.role and request.user.role.name == "Admin"))):
        return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        versions = MobileAppVersion.objects.all().order_by("-version_code", "-created_at")
        return Response([_mobile_app_version_dict(request, v) for v in versions])

    if request.method == "POST":
        data = request.data
        file_obj = request.FILES.get("file")
        version_name = data.get("version_name")
        version_code_str = data.get("version_code")
        description = data.get("description", "")
        is_active_val = data.get("is_active")

        # Convert is_active to boolean
        is_active = is_active_val in [True, "true", "True", 1, "1"]

        if not all([file_obj, version_name, version_code_str]):
            return Response({"error": "Wersiýa ady, wersiýa kody we APK faýly gerek"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            version_code = int(version_code_str)
        except ValueError:
            return Response({"error": "Wersiýa kody san bolmaly"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # If activating, deactivate all other versions first
                if is_active:
                    MobileAppVersion.objects.filter(is_active=True).update(is_active=False)

                version = MobileAppVersion.objects.create(
                    version_name=version_name,
                    version_code=version_code,
                    file=file_obj,
                    is_active=is_active,
                    description=description
                )
            return Response(_mobile_app_version_dict(request, version), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Ýalňyşlyk ýüze çykdy: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def activate_mobile_app_version(request, version_id: int):
    """Admin-only endpoint to activate a specific mobile app version."""
    if not (request.user.is_authenticated and (request.user.is_superuser or (request.user.role and request.user.role.name == "Admin"))):
        return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    try:
        version = MobileAppVersion.objects.get(id=version_id)
    except MobileAppVersion.DoesNotExist:
        return Response({"error": "Wersiýa tapylmady"}, status=status.HTTP_404_NOT_FOUND)

    try:
        with transaction.atomic():
            # Deactivate all other versions
            MobileAppVersion.objects.filter(is_active=True).update(is_active=False)
            # Activate selected version
            version.is_active = True
            version.save()
        return Response({"success": True, "version": _mobile_app_version_dict(request, version)})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT", "DELETE"])
def mobile_app_version_detail(request, version_id: int):
    """Admin-only endpoint to edit or delete a specific mobile app version."""
    if not (request.user.is_authenticated and (request.user.is_superuser or (request.user.role and request.user.role.name.lower() == "admin"))):
        return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    try:
        version = MobileAppVersion.objects.get(id=version_id)
    except MobileAppVersion.DoesNotExist:
        return Response({"error": "Wersiýa tapylmady"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        data = request.data
        file_obj = request.FILES.get("file")
        version_name = data.get("version_name")
        version_code_str = data.get("version_code")
        description = data.get("description")
        is_active_val = data.get("is_active")

        if version_name is not None:
            version.version_name = version_name
        if version_code_str is not None:
            try:
                version.version_code = int(version_code_str)
            except ValueError:
                return Response({"error": "Wersiýa kody san bolmaly"}, status=status.HTTP_400_BAD_REQUEST)
        if description is not None:
            version.description = description

        try:
            with transaction.atomic():
                if is_active_val is not None:
                    is_active = is_active_val in [True, "true", "True", 1, "1"]
                    if is_active and not version.is_active:
                        # Deactivate all other versions
                        MobileAppVersion.objects.filter(is_active=True).update(is_active=False)
                    version.is_active = is_active

                if file_obj is not None:
                    # Delete old file from disk first
                    if version.file:
                        version.file.delete(save=False)
                    version.file = file_obj

                version.save()
            return Response(_mobile_app_version_dict(request, version))
        except Exception as e:
            return Response({"error": f"Ýalňyşlyk ýüze çykdy: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # DELETE
    try:
        # Delete file from disk
        if version.file:
            version.file.delete(save=False)
        # Delete database record
        version.delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _currency_dict(currency):
    return {
        "id": currency.id,
        "name": currency.name,
        "code": currency.code,
        "symbol": currency.symbol,
        "is_active": currency.is_active,
    }


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def currencies(request):
    """
    GET: AllowAny. List all currencies.
    POST: Admin only. Create currency.
    """
    if request.method == "GET":
        items = [_currency_dict(c) for c in Currency.objects.all().order_by("id")]
        return Response(items)

    # POST (create)
    if not (request.user.is_authenticated and (request.user.is_superuser or (request.user.role and request.user.role.name.lower() == "admin"))):
        return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    name = data.get("name")
    code = data.get("code")
    symbol = data.get("symbol")
    is_active = data.get("is_active", False) in [True, "true", "True", 1, "1"]

    if not name or not code or not symbol:
        return Response({"error": "name, code, and symbol are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            if is_active:
                Currency.objects.filter(is_active=True).update(is_active=False)
            curr = Currency.objects.create(
                name=name,
                code=code,
                symbol=symbol,
                is_active=is_active
            )
        return Response(_currency_dict(curr), status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def active_currency(request):
    """
    GET: Return the currently active currency.
    """
    active = Currency.objects.filter(is_active=True).first()
    if not active:
        # Fallback to TMT
        active, _ = Currency.objects.get_or_create(
            code="TMT",
            defaults={"name": "Manat", "symbol": "TMT", "is_active": True}
        )
    return Response(_currency_dict(active))


@api_view(["PUT", "DELETE"])
def currency_detail(request, currency_id: int):
    """
    Admin only: Edit or delete a currency.
    """
    if not (request.user.is_authenticated and (request.user.is_superuser or (request.user.role and request.user.role.name.lower() == "admin"))):
        return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    try:
        curr = Currency.objects.get(id=currency_id)
    except Currency.DoesNotExist:
        return Response({"error": "Pul birligi tapylmady"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        data = request.data
        name = data.get("name")
        code = data.get("code")
        symbol = data.get("symbol")
        is_active_val = data.get("is_active")

        if name is not None:
            curr.name = name
        if code is not None:
            curr.code = code
        if symbol is not None:
            curr.symbol = symbol

        try:
            with transaction.atomic():
                if is_active_val is not None:
                    is_active = is_active_val in [True, "true", "True", 1, "1"]
                    if is_active and not curr.is_active:
                        Currency.objects.filter(is_active=True).update(is_active=False)
                    curr.is_active = is_active
                curr.save()
            return Response(_currency_dict(curr))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # DELETE
    try:
        curr.delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def activate_currency(request, currency_id: int):
    """
    Admin only: Activate a currency.
    """
    if not (request.user.is_authenticated and (request.user.is_superuser or (request.user.role and request.user.role.name.lower() == "admin"))):
        return Response({"error": "Rugsadyňyz ýok"}, status=status.HTTP_403_FORBIDDEN)

    try:
        curr = Currency.objects.get(id=currency_id)
    except Currency.DoesNotExist:
        return Response({"error": "Pul birligi tapylmady"}, status=status.HTTP_404_NOT_FOUND)

    try:
        with transaction.atomic():
            # Deactivate all
            Currency.objects.filter(is_active=True).update(is_active=False)
            curr.is_active = True
            curr.save()
        return Response({"success": True, "currency": _currency_dict(curr)})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
