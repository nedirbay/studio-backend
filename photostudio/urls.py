from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PhotoCategoryViewSet,
    PhotoCollectionViewSet,
    PhotoBlogViewSet,
    PhotoReelViewSet,
    PhotoReelCommentViewSet,
)

router = DefaultRouter()
router.register(r'categories', PhotoCategoryViewSet)
router.register(r'collections', PhotoCollectionViewSet, basename='collections')
router.register(r'blogs', PhotoBlogViewSet)
router.register(r'reels', PhotoReelViewSet, basename='reels')
router.register(r'comments', PhotoReelCommentViewSet, basename='reel-comments')

urlpatterns = [
    path('', include(router.urls)),
]
