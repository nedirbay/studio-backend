"""URL routes for the management app.

Mounted by the project under the `/api/management/` prefix (see
`studio_api/urls.py`), so these never collide with the existing `main` app's
`/api/...` routes. Auth (`/api/auth/...`) continues to be served by `identity`.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Customers
    path("customers", views.customers),
    path("customers/<int:customer_id>", views.customer_detail),
    # Appointments
    path("appointments", views.appointments),
    path("appointments/date/<str:dt>", views.appointments_by_date),
    path("appointments/<int:appointment_id>", views.appointment_detail),
    # Orders
    path("orders", views.orders),
    path("orders/<int:order_id>", views.order_detail),
    path("orders/staff/<int:user_id>", views.orders_by_staff),
    # Equipments
    path("equipments", views.equipments),
    path("equipments/assigned", views.equipments_assigned),
    path("equipments/<int:equipment_id>", views.equipment_detail),
    # Expenses
    path("expenses", views.expenses),
    path("expenses/<int:expense_id>", views.expense_detail),
    # Services
    path("services", views.services),
    path("services/<int:service_id>", views.service_detail),
    # Order types
    path("order-types", views.order_types),
    path("order-types/<int:order_type_id>", views.order_type_detail),
    # Gallery
    path("gallery", views.gallery),
    path("gallery/<int:item_id>", views.gallery_detail),
    # Attendance & stats
    path("attendance", views.attendance),
    path("stats/financial", views.financial_stats),
]
