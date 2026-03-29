from django.urls import path
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    path("api/auth/login", views.auth_login),
    path("api/auth/me", views.auth_me),
    path("api/auth/profile", views.auth_profile),
    path("api/customers", views.customers),
    path("api/customers/<int:customer_id>", views.customer_detail),
    path("api/appointments", views.appointments),
    path("api/appointments/date/<str:dt>", views.appointments_by_date),
    path("api/appointments/<int:appointment_id>", views.appointment_update),
    path("api/orders", views.orders),
    path("api/orders/<int:order_id>", views.order_detail),
    path("api/orders/staff/<int:user_id>", views.orders_by_staff),
    path("api/equipments", views.equipments),
    path("api/equipments/assigned", views.equipments_assigned),
    path("api/expenses", views.expenses),
    path("api/stats/financial", views.financial_stats),
    path("api/schema", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path(
        "api/docs",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="swagger-ui",
    ),
]
