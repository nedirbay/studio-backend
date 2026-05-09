from django.urls import path

from blog import views

urlpatterns = [
    path("api/blogs", views.blogs),
    path("api/blogs/<int:blog_id>", views.blog_detail),
]
