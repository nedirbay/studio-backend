from django.urls import path
from . import views

urlpatterns = [
    path('auth/register', views.register_view, name='register'),
    path('auth/login', views.login_view, name='login'),
    path('auth/me', views.me_view, name='me'),
]
