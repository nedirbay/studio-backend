from django.urls import path

from blog import views

urlpatterns = [
    path("api/blogs", views.blogs),
    path("api/blogs/<str:slug>", views.blog_detail),
]
