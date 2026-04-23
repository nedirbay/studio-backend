from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.AdminUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register', views.register_view, name='register'),
    path('auth/verify-otp', views.verify_otp_view, name='verify_otp'),
    path('auth/resend-otp', views.resend_otp_view, name='resend_otp'),
    path('auth/login', views.login_view, name='login'),
    path('auth/google', views.google_login_view, name='google_login'),
    path('auth/me', views.me_view, name='me'),
    path('notifications', views.notifications_view, name='notifications'),
    path('notifications/read', views.mark_notifications_read, name='notifications_read'),
    path('notifications/<int:notif_id>', views.delete_notification, name='notification_delete'),
]
