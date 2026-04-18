from django.urls import path
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    path("customers", views.customers),
    path("customers/<int:customer_id>", views.customer_detail),
    path("appointments", views.appointments),
    path("appointments/date/<str:dt>", views.appointments_by_date),
    path("appointments/<int:appointment_id>", views.appointment_update),
    path("orders", views.orders),
    path("orders/<int:order_id>", views.order_detail),
    path("orders/staff/<int:user_id>", views.orders_by_staff),
    path("equipments", views.equipments),
    path("equipments/assigned", views.equipments_assigned),
    path("expenses", views.expenses),
    path("stats/financial", views.financial_stats),
    path("banners", views.banners),
    path("promos", views.promos),
    path("schema", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path(
        "docs",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="swagger-ui",
    ),
]
