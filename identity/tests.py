from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Role, OTPCode, Notification
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
        # Django's authenticate() returns None for inactive users, so login_view falls through to 401.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_success_with_active_user(self):
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('jwt', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_wrong_password(self):
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'WRONG',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_otp_verification(self):
        user = User.objects.create_user(**self.user_data)
        user.is_active = False
        user.save()
        OTPCode.objects.create(
            user=user,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        response = self.client.post(reverse('verify_otp'), {
            'email': user.email,
            'code': '123456',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_otp_wrong_code_rejected(self):
        user = User.objects.create_user(**self.user_data)
        OTPCode.objects.create(user=user, code='111111', expires_at=timezone.now() + timedelta(minutes=10))
        response = self.client.post(reverse('verify_otp'), {'email': user.email, 'code': '222222'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_otp_expired_rejected(self):
        user = User.objects.create_user(**self.user_data)
        OTPCode.objects.create(user=user, code='123456', expires_at=timezone.now() - timedelta(minutes=1))
        response = self.client.post(reverse('verify_otp'), {'email': user.email, 'code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_missing_fields(self):
        response = self.client.post(reverse('verify_otp'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_otp_for_unverified_user(self):
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = False
        user.is_active = False
        user.save()
        response = self.client.post(reverse('resend_otp'), {'email': user.email})
        # email may or may not succeed depending on smtp; both 200 and 500 are acceptable for the test env
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])
        self.assertTrue(OTPCode.objects.filter(user=user).exists())

    def test_resend_otp_user_not_found(self):
        response = self.client.post(reverse('resend_otp'), {'email': 'nouser@example.com'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_view(self):
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_me_requires_authentication(self):
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_password_full_flow(self):
        user = User.objects.create_user(**self.user_data)
        OTPCode.objects.create(user=user, code='999000', expires_at=timezone.now() + timedelta(minutes=10))
        response = self.client.post(reverse('reset_password'), {
            'email': user.email,
            'code': '999000',
            'new_password': 'BrandNewPass1',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password('BrandNewPass1'))

    def test_reset_password_invalid_code(self):
        user = User.objects.create_user(**self.user_data)
        OTPCode.objects.create(user=user, code='999000', expires_at=timezone.now() + timedelta(minutes=10))
        response = self.client.post(reverse('reset_password'), {
            'email': user.email,
            'code': '000000',
            'new_password': 'BrandNewPass1',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_missing_fields(self):
        response = self.client.post(reverse('reset_password'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_google_login_missing_credential(self):
        response = self.client.post(reverse('google_login'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notif-user', email='notif@example.com', password='pass123', is_active=True
        )
        Notification.objects.create(user=self.user, title='Hi', message='Welcome', type='system')
        Notification.objects.create(user=self.user, title='Update', message='New feature', type='system')

    def test_list_notifications(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_mark_notifications_read(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse('notifications_read'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_delete_notification(self):
        self.client.force_authenticate(self.user)
        notif = Notification.objects.filter(user=self.user).first()
        response = self.client.delete(reverse('notification_delete', args=[notif.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Notification.objects.filter(id=notif.id).exists())

    def test_notifications_require_authentication(self):
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminUserViewSetTests(APITestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Admin')
        self.admin = User.objects.create_user(
            username='admin', email='admin@example.com', password='pass123', is_active=True
        )

    def test_list_users_requires_auth(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_via_admin_viewset(self):
        self.client.force_authenticate(self.admin)
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123',
            'role_input': 'Staff',
            'is_active': True,
        }
        response = self.client.post('/api/users/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username='newuser')
        self.assertTrue(created.check_password('NewPass123'))
        self.assertEqual(created.role.name, 'Staff')
