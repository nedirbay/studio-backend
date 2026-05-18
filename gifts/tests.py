from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from identity.models import Role, User

from .models import Campaign, CampaignParticipation, CampaignRule


class GiftsApiTests(APITestCase):
    def setUp(self):
        role = Role.objects.create(name="customer")
        self.user = User.objects.create_user(
            username="gift-user",
            email="gift@example.com",
            password="password123",
            role=role,
            is_active=True,
        )
        self.campaign = Campaign.objects.create(
            type="giveaway",
            title="Camera Giveaway",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=7),
            is_featured=True,
            status="active",
        )
        CampaignRule.objects.create(campaign=self.campaign, text="Follow the page", order=1)
        CampaignRule.objects.create(campaign=self.campaign, text="Tag a friend", order=2)

    def test_campaigns_list_and_featured(self):
        response = self.client.get("/api/gifts/campaigns/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Camera Giveaway")
        self.assertEqual(len(response.data[0]["rules_list"]), 2)
        self.assertTrue(response.data[0]["is_active"])

        featured = self.client.get("/api/gifts/campaigns/featured/")
        self.assertEqual(featured.status_code, status.HTTP_200_OK)
        self.assertEqual(len(featured.data), 1)

    def test_anonymous_join_validation_and_success(self):
        response = self.client.post(f"/api/gifts/campaigns/{self.campaign.id}/join/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            f"/api/gifts/campaigns/{self.campaign.id}/join/",
            {"full_name": "Anon User", "phone": "+99361000000", "email": "anon@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CampaignParticipation.objects.count(), 1)

    def test_authenticated_user_cannot_join_twice(self):
        self.client.force_authenticate(self.user)

        first = self.client.post(f"/api/gifts/campaigns/{self.campaign.id}/join/", {}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(f"/api/gifts/campaigns/{self.campaign.id}/join/", {}, format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_join_inactive_campaign_rejected(self):
        inactive = Campaign.objects.create(
            type="giveaway",
            title="Old",
            starts_at=timezone.now() - timedelta(days=10),
            ends_at=timezone.now() - timedelta(days=1),
            status="finished",
        )
        response = self.client.post(
            f"/api/gifts/campaigns/{inactive.id}/join/",
            {"full_name": "X", "phone": "+99361"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_campaign_type_filter(self):
        Campaign.objects.create(
            type="promotion", title="Promo", starts_at=timezone.now(), status="active"
        )
        Campaign.objects.create(
            type="gift", title="Gift", starts_at=timezone.now(), status="active"
        )

        response = self.client.get("/api/gifts/campaigns/?type=promotion")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item["type"], "promotion")

    def test_campaign_status_filter(self):
        Campaign.objects.create(
            type="giveaway", title="Draft", starts_at=timezone.now(), status="draft"
        )
        response = self.client.get("/api/gifts/campaigns/?status=draft")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item["status"], "draft")

    def test_campaign_join_list_get(self):
        # GET on join action should return participants
        CampaignParticipation.objects.create(
            campaign=self.campaign, full_name="Joe", phone="+99361"
        )
        response = self.client.get(f"/api/gifts/campaigns/{self.campaign.id}/join/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_campaign_is_active_property(self):
        self.assertTrue(self.campaign.is_active)
        future = Campaign.objects.create(
            type="giveaway",
            title="Future",
            starts_at=timezone.now() + timedelta(days=5),
            ends_at=timezone.now() + timedelta(days=10),
            status="active",
        )
        self.assertFalse(future.is_active)
