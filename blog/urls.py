from django.urls import path

from blog import views

urlpatterns = [
    path("api/blogs", views.blogs),
    path("api/blogs/<str:blog_identifier>", views.blog_detail),
]
