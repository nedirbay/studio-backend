from django.urls import path

from commerce import views

urlpatterns = [
    path("categories", views.categories),
    path("products", views.products),
    path("brands", views.brands),
    path("products/<int:product_id>", views.product_detail),
    path("upload", views.upload_image),
]
urlpatterns += [
    path("products/<int:product_id>/reviews", views.product_reviews),
    path("reviews", views.all_reviews),
    path("reviews/<int:review_id>", views.review_detail),
    path("messages", views.contact_messages),
    path("messages/<int:message_id>", views.contact_message_detail),
]
