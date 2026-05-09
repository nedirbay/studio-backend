from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Role, OTPCode
from django.utils import timezone
from datetime import timedelta

class IdentityTests(APITestCase):
    def setUp(self):
        self.customer_role = Role.objects.create(name='Customer')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

    def test_registration(self):
        url = reverse('register')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertTrue(OTPCode.objects.filter(user=user).exists())

    def test_login_failed_if_inactive(self):
        user = User.objects.create_user(**self.user_data)
        user.is_active = False
        user.save()
        url = reverse('login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_otp_verification(self):
        user = User.objects.create_user(**self.user_data)
        user.is_active = False
        user.save()
        otp = OTPCode.objects.create(
            user=user, 
            code='123456', 
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        url = reverse('verify_otp')
        response = self.client.post(url, {
            'email': user.email,
            'code': '123456'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_me_view(self):
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        url = reverse('me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
