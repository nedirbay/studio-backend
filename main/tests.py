import json
from datetime import date
from decimal import Decimal

from django.test import Client, TestCase

from identity.models import Role, User


from .models import (
    Appointment,
    Banner,
    Customer,
    Equipment,
    EquipmentAssignment,
    Expense,
    Order,
    OrderDay,
    OrderType,
    Promo,
)
from .services import OrderService
from rest_framework_simplejwt.tokens import RefreshToken


class ApiEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # seed role/user
        self.role = Role.objects.create(name="admin")
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="password123",
            role=self.role,
            salary=Decimal("1000.00"),
            phone="555-000",
        )
        self.jwt = self._issue_jwt(self.user)
        # seed customer and appointment
        self.customer = Customer.objects.create(name="Alice", phone="111")
        self.appt = Appointment.objects.create(
            customer=self.customer,
            date=date(2025, 1, 1),
            time="10:00",
            service_type="shoot",
        )
        self.ot = OrderType.objects.create(name="Studio")

    def _issue_jwt(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def auth_headers(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.jwt}"}

    def test_customers_list_and_create(self):
        resp = self.client.get("/api/customers", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

        resp = self.client.post(
            "/api/customers",
            data=json.dumps({"name": "Bob", "phone": "222"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 201)
        new_id = resp.json()["id"]
        self.assertTrue(Customer.objects.filter(id=new_id).exists())

    def test_customer_update_delete_and_validation(self):
        # validation
        resp = self.client.post(
            "/api/customers",
            data=json.dumps({"name": "NoPhone"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 400)
        # create, update, delete
        cid = Customer.objects.create(name="Temp", phone="333").id
        resp = self.client.put(
            f"/api/customers/{cid}",
            data=json.dumps({"name": "Temp2"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Customer.objects.get(id=cid).name, "Temp2")
        resp = self.client.delete(f"/api/customers/{cid}", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Customer.objects.filter(id=cid).exists())

    def test_appointments_by_date(self):
        resp = self.client.get("/api/appointments/date/2025-01-01", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["customer_id"], self.customer.id)

    def test_appointment_create_and_update_validation(self):
        # missing fields
        resp = self.client.post(
            "/api/appointments", data=json.dumps({}), content_type="application/json", **self.auth_headers()
        )
        self.assertEqual(resp.status_code, 400)
        # create
        resp = self.client.post(
            "/api/appointments",
            data=json.dumps(
                {
                    "customer_id": self.customer.id,
                    "date": "2025-02-01",
                    "time": "12:00",
                    "service_type": "edit",
                }
            ),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 201)
        appt_id = resp.json()["id"]
        # update
        resp = self.client.put(
            f"/api/appointments/{appt_id}",
            data=json.dumps({"status": "tassyklandy", "time": "13:00"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Appointment.objects.get(id=appt_id).status, "tassyklandy")

    def test_orders_create_and_detail(self):
        # create order
        payload = {
            "customer_name": "Alice",
            "customer_phone": "111",
            "total_amount": 100,
            "paid_amount": 50,
            "order_type_id": self.ot.id,
            "days": [
                {"date": "2025-01-02", "address": "Addr", "daily_price": 100, "time": "09:00"}
            ],
            "staff": [{"user_id": self.user.id, "role": "photographer"}],
        }
        resp = self.client.post(
            "/api/orders", data=json.dumps(payload), content_type="application/json", **self.auth_headers()
        )
        self.assertEqual(resp.status_code, 201)
        order_id = resp.json()["id"]

        # detail
        resp = self.client.get(f"/api/orders/{order_id}", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["customer_name"], "Alice")
        self.assertEqual(len(data["days"]), 1)
        self.assertEqual(len(data["staff"]), 1)

    def test_orders_update_delete_staff_filter_and_validation(self):
        # validation missing fields
        resp = self.client.post(
            "/api/orders",
            data=json.dumps({"customer_phone": "111"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 400)

        # create base order
        order = Order.objects.create(
            customer_name="Alice",
            customer_phone="111",
            total_amount=Decimal("200"),
            paid_amount=Decimal("20"),
        )
        OrderDay.objects.create(order=order, date=date(2025, 3, 1), address="Addr", daily_price=Decimal("200"))
        # update
        payload = {
            "customer_name": "Alice U",
            "customer_phone": "999",
            "total_amount": 300,
            "paid_amount": 150,
            "days": [{"date": "2025-03-02", "address": "New", "daily_price": 300}],
            "staff": [{"user_id": self.user.id, "role": "camera"}],
        }
        resp = self.client.put(
            f"/api/orders/{order.id}",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.paid_amount, Decimal("150"))
        self.assertEqual(order.days.count(), 1)
        # staff filter
        resp = self.client.get(f"/api/orders/staff/{self.user.id}", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(o["id"] == order.id for o in resp.json()))
        # delete
        resp = self.client.delete(f"/api/orders/{order.id}", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_expense_and_stats(self):
        # create expense
        resp = self.client.post(
            "/api/expenses",
            data=json.dumps({"amount": 20, "date": "2025-01-03", "description": "rent"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 201)

        # create order with paid amount to reflect income
        payload = {
            "customer_name": "Alice",
            "customer_phone": "111",
            "total_amount": 100,
            "paid_amount": 80,
            "days": [{"date": "2025-01-04", "address": "Addr", "daily_price": 100}],
            "staff": [],
        }
        resp = self.client.post(
            "/api/orders", data=json.dumps(payload), content_type="application/json", **self.auth_headers()
        )
        self.assertEqual(resp.status_code, 201)

        resp = self.client.get("/api/stats/financial", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        stats = resp.json()
        self.assertEqual(stats["total_income"], 80.0)
        self.assertEqual(stats["total_expense"], 20.0)
        self.assertEqual(stats["net"], 60.0)

    def test_equipments_endpoints(self):
        # create
        resp = self.client.post(
            "/api/equipments",
            data=json.dumps({"name": "Light", "count": 2}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(resp.status_code, 201)
        eq_id = resp.json()["id"]
        self.assertTrue(Equipment.objects.filter(id=eq_id).exists())
        # list
        resp = self.client.get("/api/equipments", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()), 1)
        # assigned
        EquipmentAssignment.objects.create(equipment_id=eq_id, user=self.user, count=1)
        resp = self.client.get("/api/equipments/assigned", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertTrue(any(item["equipment_id"] == eq_id for item in items))

    def test_order_types(self):
        resp = self.client.get("/api/order-types", **self.auth_headers())
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post(
            "/api/order-types",
            data=json.dumps({"name": "Wedding"}),
            content_type="application/json",
            **self.auth_headers()
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(OrderType.objects.filter(name="Wedding").exists())

    def test_banners_crud_and_promos_list(self):
        banner_payload = {
            "title": "Camera Banner",
            "subtitle": "Fresh stock",
            "description": "Latest cameras",
            "image": "https://example.com/banner.jpg",
            "ctaText": "Shop now",
            "bgColor": "from-red-900/80",
        }
        create_response = self.client.post(
            "/api/banners",
            data=json.dumps(banner_payload),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        banner_id = create_response.json()["id"]

        list_response = self.client.get("/api/banners")
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(any(item["id"] == banner_id for item in list_response.json()))

        update_response = self.client.put(
            "/api/banners",
            data=json.dumps({"id": banner_id, "title": "Updated Camera Banner"}),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(Banner.objects.get(id=banner_id).title, "Updated Camera Banner")

        delete_response = self.client.delete(
            "/api/banners",
            data=json.dumps({"id": banner_id}),
            content_type="application/json",
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Banner.objects.filter(id=banner_id).exists())

        Promo.objects.create(
            title="Lens promo",
            subtitle="Top deals",
            badge="Sale",
            image_url="https://example.com/promo.jpg",
        )
        promo_response = self.client.get("/api/promos")
        self.assertEqual(promo_response.status_code, 200)
        self.assertEqual(len(promo_response.json()), 1)


class ServiceLayerTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="admin")
        self.user = User.objects.create_user(
            username="tester2",
            password="password123",
            role=self.role,
            salary=Decimal("500.00"),
        )
        self.order = Order.objects.create(
            customer_name="Alice",
            customer_phone="111",
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("40.00"),
        )
        self.expense = Expense.objects.create(amount=Decimal("10.00"), date=date(2025, 1, 5), description="test")

    def test_order_financial_stats(self):
        svc = OrderService()
        stats = svc.get_financial_stats()
        self.assertEqual(stats.total_income, Decimal("40.00"))
        self.assertEqual(stats.total_expense, Decimal("10.00"))
        self.assertEqual(stats.net, Decimal("30.00"))

    def test_order_remaining_amount_property(self):
        self.assertEqual(self.order.remaining_amount, Decimal("60.00"))

    def test_financial_stats_with_date_range(self):
        svc = OrderService()
        stats = svc.get_financial_stats(start=date(2025, 1, 10), end=date(2025, 1, 31))
        # expense was on Jan 5 so it should be excluded
        self.assertEqual(stats.total_expense, Decimal("0"))


class EdgeCaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role = Role.objects.create(name="staff")
        self.user = User.objects.create_user(
            username="edge", email="e@example.com", password="pass123", role=self.role
        )
        self.jwt = str(RefreshToken.for_user(self.user).access_token)

    def auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.jwt}"}

    def test_customer_detail_not_found(self):
        resp = self.client.get("/api/customers/99999", **self.auth())
        self.assertEqual(resp.status_code, 404)

    def test_customer_update_not_found(self):
        resp = self.client.put(
            "/api/customers/99999",
            data=json.dumps({"name": "X"}),
            content_type="application/json",
            **self.auth(),
        )
        self.assertEqual(resp.status_code, 404)

    def test_customer_delete_not_found(self):
        resp = self.client.delete("/api/customers/99999", **self.auth())
        self.assertEqual(resp.status_code, 404)

    def test_order_detail_not_found(self):
        resp = self.client.get("/api/orders/99999", **self.auth())
        self.assertEqual(resp.status_code, 404)

    def test_appointments_invalid_date_format(self):
        resp = self.client.get("/api/appointments/date/not-a-date", **self.auth())
        self.assertEqual(resp.status_code, 400)

    def test_equipments_missing_fields(self):
        resp = self.client.post(
            "/api/equipments",
            data=json.dumps({}),
            content_type="application/json",
            **self.auth(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_expense_missing_fields(self):
        resp = self.client.post(
            "/api/expenses",
            data=json.dumps({"amount": 50}),
            content_type="application/json",
            **self.auth(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_protected_endpoints_require_jwt(self):
        # No auth header
        for url in ["/api/customers", "/api/appointments", "/api/orders", "/api/equipments", "/api/expenses"]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 401, msg=url)

    def test_banner_update_missing_id(self):
        resp = self.client.put(
            "/api/banners",
            data=json.dumps({"title": "no-id"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_banner_update_not_found(self):
        resp = self.client.put(
            "/api/banners",
            data=json.dumps({"id": 99999, "title": "X"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_order_type_create_validation(self):
        resp = self.client.post(
            "/api/order-types",
            data=json.dumps({}),
            content_type="application/json",
            **self.auth(),
        )
        self.assertEqual(resp.status_code, 400)
