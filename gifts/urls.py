from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampaignViewSet, CampaignParticipationViewSet


router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaigns')
router.register(r'participations', CampaignParticipationViewSet, basename='participations')


urlpatterns = [
    path('', include(router.urls)),
]
