from django.urls import path
from . import views

urlpatterns = [
    path('auth/register', views.register_view, name='register'),
    path('auth/verify-otp', views.verify_otp_view, name='verify_otp'),
    path('auth/resend-otp', views.resend_otp_view, name='resend_otp'),
    path('auth/login', views.login_view, name='login'),
    path('auth/me', views.me_view, name='me'),
]
