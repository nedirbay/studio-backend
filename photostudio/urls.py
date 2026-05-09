from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhotoCategoryViewSet, PhotoBlogViewSet

router = DefaultRouter()
router.register(r'categories', PhotoCategoryViewSet)
router.register(r'blogs', PhotoBlogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
