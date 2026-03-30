from django.urls import path

from . import views

urlpatterns = [
    path("api/auth/login", views.auth_login),
    path("api/auth/me", views.auth_me),
    path("api/auth/profile", views.auth_profile),
    path("api/auth/refresh", views.auth_refresh),
]
