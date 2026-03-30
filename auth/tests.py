import json
from decimal import Decimal

from django.test import Client, TestCase

from auth.models import Role, User
from auth.services import AuthService
from auth.views import _issue_jwt as issue_jwt, _issue_refresh_jwt as issue_refresh_jwt


class AuthEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role = Role.objects.create(name="admin")
        self.user = User.objects.create(
            name="Tester",
            token="tok123",
            role=self.role,
            salary=Decimal("1000.00"),
            phone="555-000",
        )
        self.jwt = issue_jwt(self.user)
        self.refresh = issue_refresh_jwt(self.user)

    def auth_headers(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.jwt}"}

    def test_auth_login(self):
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"token": "tok123"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["id"], self.user.id)
        self.assertEqual(payload["role"], "admin")
        self.assertIn("jwt", payload)
        self.assertIn("refresh", payload)

    def test_auth_refresh(self):
        resp = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh": self.refresh}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("jwt", data)
        self.assertIn("refresh", data)

    def test_auth_login_invalid(self):
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"token": "bad"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_auth_me_and_profile(self):
        resp = self.client.get("/api/auth/me", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "Tester")
        resp = self.client.put(
            "/api/auth/profile",
            data=json.dumps({"phone": "999", "salary": 1500}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "999")
        self.assertEqual(self.user.salary, Decimal("1500"))


class AuthServiceTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="admin")
        self.user = User.objects.create(
            name="Tester",
            token="tok123",
            role=self.role,
            salary=Decimal("500.00"),
        )

    def test_auth_change_token(self):
        svc = AuthService()
        ok = svc.change_token(self.user.id, "tok123", "tok999")
        self.assertTrue(ok)
        self.assertEqual(User.objects.get(id=self.user.id).token, "tok999")
