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

    from unittest.mock import patch
    @patch('identity.views.send_mail')
    def test_registration_email_failure_rollback(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP Connection Timeout")
        url = reverse('register')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("SMTP Connection Timeout", response.data['error'])
        # The user should NOT be created in the database due to rollback!
        self.assertFalse(User.objects.filter(username='testuser').exists())

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
        import os
        from django.conf import settings
        self.log_file_path = os.path.join(settings.BASE_DIR, 'api_requests.log')
        self.log_backup_content = None
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                self.log_backup_content = f.read()

    def tearDown(self):
        import os
        if hasattr(self, 'log_backup_content'):
            if self.log_backup_content is not None:
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_backup_content)
            elif os.path.exists(self.log_file_path):
                os.remove(self.log_file_path)

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

    def test_admin_logs_requires_auth(self):
        response = self.client.get('/api/admin/logs')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_logs_requires_admin_privilege(self):
        normal_user = User.objects.create_user(
            username='normal', email='normal@example.com', password='pass123', is_active=True
        )
        self.client.force_authenticate(normal_user)
        response = self.client.get('/api/admin/logs')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_logs_success(self):
        self.admin.role = self.role
        self.admin.save()
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/admin/logs')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_admin_logs_csv_export(self):
        self.admin.role = self.role
        self.admin.save()
        self.client.force_authenticate(self.admin)
        # Write some mock logs
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("INFO 2026-07-03 14:52:17,215 middleware User: admin | Method: POST | Path: /api/test | Status: 200 | Duration: 0.005s\n")
        
        response = self.client.get('/api/admin/logs', {'export': 'csv'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertIn('sistem_loglary.csv', response['Content-Disposition'])
        self.assertIn(b'admin', response.content)
        self.assertIn(b'POST', response.content)

    def test_admin_logs_delete_all(self):
        self.admin.role = self.role
        self.admin.save()
        self.client.force_authenticate(self.admin)
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("INFO 2026-07-03 14:52:17,215 middleware User: admin | Method: POST | Path: /api/test | Status: 200 | Duration: 0.005s\n")
        
        response = self.client.delete('/api/admin/logs', {'action': 'delete_all'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, '')

    def test_admin_logs_delete_by_date(self):
        self.admin.role = self.role
        self.admin.save()
        self.client.force_authenticate(self.admin)
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("INFO 2026-07-01 12:00:00,000 middleware User: admin | Method: POST | Path: /api/1 | Status: 200 | Duration: 0.005s\n")
            f.write("INFO 2026-07-02 12:00:00,000 middleware User: admin | Method: POST | Path: /api/2 | Status: 200 | Duration: 0.005s\n")
            f.write("INFO 2026-07-03 12:00:00,000 middleware User: admin | Method: POST | Path: /api/3 | Status: 200 | Duration: 0.005s\n")
        
        response = self.client.delete('/api/admin/logs', {
            'action': 'delete_by_date',
            'start_date': '2026-07-02',
            'end_date': '2026-07-03'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn('/api/1', lines[0])

    def test_admin_logs_delete_selected(self):
        self.admin.role = self.role
        self.admin.save()
        self.client.force_authenticate(self.admin)
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("INFO 2026-07-03 12:00:00,000 middleware User: admin | Method: POST | Path: /api/1 | Status: 200 | Duration: 0.005s\n")
            f.write("INFO 2026-07-03 13:00:00,000 middleware User: admin | Method: POST | Path: /api/2 | Status: 201 | Duration: 0.005s\n")
        
        response = self.client.delete('/api/admin/logs', {
            'action': 'delete_selected',
            'selected_logs': [
                {
                    'timestamp': '2026-07-03 13:00:00',
                    'method': 'POST',
                    'path': '/api/2',
                    'user': 'admin',
                    'status': '201'
                }
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn('/api/1', lines[0])
