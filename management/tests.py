"""Tests for the management app API.

Covers the endpoints the Flutter `news_app` relies on: customers, appointments,
orders (with nested days/equipments/services/staff), equipments, expenses,
services, order-types, gallery, attendance and financial stats.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Customer, Equipment, Expense, Order, OrderType, Service

User = get_user_model()

BASE = "/api/management"


class ManagementApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="worker", email="worker@example.com", password="pass1234"
        )
        self.client.force_authenticate(user=self.user)

    # --- auth guard -------------------------------------------------------
    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"{BASE}/customers").status_code, 401)

    # --- customers --------------------------------------------------------
    def test_customer_crud(self):
        resp = self.client.post(
            f"{BASE}/customers", {"name": "Aman", "phone": "+99361000000"}, format="json"
        )
        self.assertEqual(resp.status_code, 201)
        cid = resp.data["id"]

        listed = self.client.get(f"{BASE}/customers")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)
        self.assertEqual(listed.data[0]["name"], "Aman")

        upd = self.client.put(
            f"{BASE}/customers/{cid}", {"name": "Aman B."}, format="json"
        )
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(Customer.objects.get(id=cid).name, "Aman B.")

        self.assertEqual(self.client.delete(f"{BASE}/customers/{cid}").status_code, 200)
        self.assertFalse(Customer.objects.filter(id=cid).exists())

    def test_customer_create_requires_fields(self):
        resp = self.client.post(f"{BASE}/customers", {"name": "x"}, format="json")
        self.assertEqual(resp.status_code, 400)

    # --- appointments -----------------------------------------------------
    def test_appointment_flow(self):
        customer = Customer.objects.create(name="Maral", phone="123")
        resp = self.client.post(
            f"{BASE}/appointments",
            {
                "customer_id": customer.id,
                "date": "2026-06-10",
                "time": "12:00",
                "service_type": "toý",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        aid = resp.data["id"]

        by_date = self.client.get(f"{BASE}/appointments/date/2026-06-10")
        self.assertEqual(by_date.status_code, 200)
        self.assertEqual(len(by_date.data), 1)
        self.assertEqual(by_date.data[0]["customer_name"], "Maral")
        self.assertEqual(by_date.data[0]["customer_phone"], "123")

        upd = self.client.put(
            f"{BASE}/appointments/{aid}", {"status": "tassyklandy"}, format="json"
        )
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(
            self.client.get(f"{BASE}/appointments")
            .data[0]["status"],
            "tassyklandy",
        )
        self.assertEqual(self.client.delete(f"{BASE}/appointments/{aid}").status_code, 200)

    # --- orders (nested) --------------------------------------------------
    def test_order_with_nested_days_and_staff(self):
        equipment = Equipment.objects.create(name="Kamera", count=5)
        service = Service.objects.create(name="Montaž")
        order_type = OrderType.objects.create(name="Toý")

        payload = {
            "customer_name": "Test Müşderi",
            "customer_phone": "+99362000000",
            "total_amount": 1000,
            "paid_amount": 400,
            "order_type_id": order_type.id,
            "days": [
                {
                    "date": "2026-07-01",
                    "address": "Aşgabat",
                    "daily_price": 500,
                    "time": "10:00",
                    "equipments": [],
                    "services": [{"service_id": service.id, "count": 1}],
                }
            ],
            "staff": [
                {
                    "user_id": self.user.id,
                    "equipments": [{"equipment_id": equipment.id, "count": 1}],
                }
            ],
        }
        resp = self.client.post(f"{BASE}/orders", payload, format="json")
        self.assertEqual(resp.status_code, 201)
        oid = resp.data["id"]

        detail = self.client.get(f"{BASE}/orders/{oid}")
        self.assertEqual(detail.status_code, 200)
        data = detail.data
        self.assertEqual(data["remaining_amount"], 600.0)
        self.assertEqual(data["order_type_id"], order_type.id)
        self.assertEqual(len(data["days"]), 1)
        self.assertEqual(len(data["days"][0]["equipments"]), 0)
        self.assertEqual(data["days"][0]["services"][0]["service_name"], "Montaž")
        self.assertEqual(len(data["staff"]), 1)
        self.assertEqual(data["staff"][0]["user_id"], self.user.id)
        self.assertEqual(data["staff"][0]["equipments"][0]["equipment_name"], "Kamera")

        # staff filter
        by_staff = self.client.get(f"{BASE}/orders/staff/{self.user.id}")
        self.assertEqual(len(by_staff.data), 1)

        # update replaces nested rows
        payload["paid_amount"] = 1000
        payload["days"] = []
        payload["staff"] = []
        upd = self.client.put(f"{BASE}/orders/{oid}", payload, format="json")
        self.assertEqual(upd.status_code, 200)
        refreshed = self.client.get(f"{BASE}/orders/{oid}").data
        self.assertEqual(refreshed["remaining_amount"], 0.0)
        self.assertEqual(refreshed["days"], [])
        
        # default status is pending
        self.assertEqual(refreshed["status"], "pending")

        # test PATCH status to approved
        patch_resp = self.client.patch(f"{BASE}/orders/{oid}", {"status": "approved"}, format="json")
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.data["status"], "approved")
        self.assertEqual(Order.objects.get(id=oid).status, "approved")

        self.assertEqual(self.client.delete(f"{BASE}/orders/{oid}").status_code, 200)
        self.assertFalse(Order.objects.filter(id=oid).exists())

    # --- equipments -------------------------------------------------------
    def test_equipment_crud(self):
        resp = self.client.post(
            f"{BASE}/equipments", {"name": "Tripod", "count": 3}, format="json"
        )
        self.assertEqual(resp.status_code, 201)
        eid = resp.data["id"]
        self.assertEqual(self.client.get(f"{BASE}/equipments").data[0]["count"], 3)
        self.client.put(f"{BASE}/equipments/{eid}", {"count": 7}, format="json")
        self.assertEqual(Equipment.objects.get(id=eid).count, 7)
        self.assertEqual(self.client.get(f"{BASE}/equipments/assigned").status_code, 200)
        self.assertEqual(self.client.delete(f"{BASE}/equipments/{eid}").status_code, 200)

    # --- expenses & stats -------------------------------------------------
    def test_expenses_and_financial_stats(self):
        Order.objects.create(
            customer_name="X", customer_phone="1", total_amount=Decimal("500"),
            paid_amount=Decimal("500"),
        )
        resp = self.client.post(
            f"{BASE}/expenses",
            {"amount": 200, "date": "2026-06-09", "description": "benzin"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Expense.objects.count(), 1)

        stats = self.client.get(f"{BASE}/stats/financial")
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.data["total_income"], 500.0)
        self.assertEqual(stats.data["total_expense"], 200.0)
        self.assertEqual(stats.data["net"], 300.0)

    # --- services & order types ------------------------------------------
    def test_services_and_order_types(self):
        s = self.client.post(f"{BASE}/services", {"name": "Drone"}, format="json")
        self.assertEqual(s.status_code, 201)
        self.assertEqual(self.client.get(f"{BASE}/services").data[0]["name"], "Drone")
        self.client.put(f"{BASE}/services/{s.data['id']}", {"name": "Dron"}, format="json")
        self.assertEqual(Service.objects.get(id=s.data["id"]).name, "Dron")
        self.assertEqual(self.client.delete(f"{BASE}/services/{s.data['id']}").status_code, 200)

        t = self.client.post(f"{BASE}/order-types", {"name": "Doglan gün"}, format="json")
        self.assertEqual(t.status_code, 201)
        self.assertEqual(self.client.get(f"{BASE}/order-types").data[0]["name"], "Doglan gün")

    # --- attendance -------------------------------------------------------
    def test_attendance(self):
        order = Order.objects.create(
            customer_name="X", customer_phone="1", total_amount=0, paid_amount=0
        )
        resp = self.client.post(
            f"{BASE}/attendance",
            {"order_id": order.id, "user_id": self.user.id, "date": "2026-06-09"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        listed = self.client.get(f"{BASE}/attendance?order_id={order.id}")
        self.assertEqual(len(listed.data), 1)
        self.assertEqual(listed.data[0]["user_name"], "worker")
