from django.urls import path

from commerce import views

urlpatterns = [
    path("categories", views.categories),
    path("categories/<int:category_id>", views.category_detail),
    path("products", views.products),
    path("brands", views.brands),
    path("brands/<int:brand_id>", views.brand_detail),
    path("products/<int:product_id>", views.product_detail),
    path("upload", views.upload_image),
]
urlpatterns += [
    path("products/<int:product_id>/reviews", views.product_reviews),
    path("reviews", views.all_reviews),
    path("reviews/<int:review_id>", views.review_detail),
    path("messages", views.contact_messages),
    path("messages/<int:message_id>", views.contact_message_detail),
    path("orders", views.OrderViewSet.as_view({'get': 'list', 'post': 'create'})),
    path("orders/<int:pk>", views.OrderViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]
