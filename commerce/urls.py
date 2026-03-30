from django.urls import path

from commerce import views

urlpatterns = [
    path("api/categories", views.categories),
    path("api/products", views.products),
    path("api/products/<int:product_id>", views.product_detail),
]
