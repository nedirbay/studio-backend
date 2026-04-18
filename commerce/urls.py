from django.urls import path

from commerce import views

urlpatterns = [
    path("categories", views.categories),
    path("products", views.products),
    path("brands", views.brands),
    path("products/<int:product_id>", views.product_detail),
]
