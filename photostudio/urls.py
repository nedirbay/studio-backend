from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PhotoStudioImageViewSet, PhotoStudioVideoViewSet


router = DefaultRouter()
router.register(r"videos", PhotoStudioVideoViewSet, basename="photostudio-videos")
router.register(r"images", PhotoStudioImageViewSet, basename="photostudio-images")

urlpatterns = [
    path("", include(router.urls)),
]
