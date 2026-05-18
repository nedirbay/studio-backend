import json
from decimal import Decimal

from django.test import Client, TestCase
from rest_framework.test import APITestCase

from commerce.models import Brand, Category, ContactMessage, Order, OrderItem, Product, ProductMedia, Review
from identity.models import Notification, Role, User


class CommerceEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Camera",
            price=Decimal("100.00"),
            category=self.category,
            instock=True,
            marka="Canon",
        )
        ProductMedia.objects.create(product=self.product, kind="image", url="/img/cam.jpg")

    def test_categories_list_create(self):
        resp = self.client.get("/api/commerce/categories")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()), 1)

        resp = self.client.post("/api/commerce/categories", data=json.dumps({"name": "Lenses"}), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Category.objects.filter(name="Lenses").exists())

    def test_products_list_create(self):
        payload = {
            "name": "Lens",
            "price": "50.00",
            "instock": False,
            "category": self.category.id,
            "marka": "Sigma",
            "media": [
                {"kind": "image", "url": "/img/lens1.jpg"},
                {"kind": "video", "url": "https://vid.com/1"},
            ],
        }
        resp = self.client.post("/api/commerce/products", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        new_id = resp.json()["id"]
        prod = Product.objects.get(id=new_id)
        self.assertEqual(prod.media.count(), 2)

    def test_product_detail_update_delete(self):
        resp = self.client.get(f"/api/commerce/products/{self.product.id}")
        self.assertEqual(resp.status_code, 200)
        # update instock and replace media with one video
        payload = {"instock": False, "media": [{"kind": "video", "url": "vid.mp4"}]}
        resp = self.client.put(
            f"/api/commerce/products/{self.product.id}", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.instock)
        self.assertEqual(self.product.media.count(), 1)
        # delete
        resp = self.client.delete(f"/api/commerce/products/{self.product.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_order_creation(self):
        payload = {
            "full_name": "Merdan",
            "phone_number": "123456",
            "items": [
                {"product": self.product.id, "quantity": 2}
            ]
        }
        resp = self.client.post("/api/commerce/orders", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["full_name"], "Merdan")
        self.assertEqual(float(resp.json()["total_price"]), 200.0)

    def test_product_detail_not_found(self):
        resp = self.client.get("/api/commerce/products/99999")
        self.assertEqual(resp.status_code, 404)

    def test_product_create_invalid_category(self):
        payload = {"name": "Bad", "price": "10.00", "category": 9999}
        resp = self.client.post("/api/commerce/products", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_brands_list(self):
        Brand.objects.create(name="Canon", slug="canon", logo_url="/img/canon.png")
        resp = self.client.get("/api/commerce/brands")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Canon")


class ReviewTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Cameras")
        self.product = Product.objects.create(
            name="DSLR", price=Decimal("500.00"), category=self.category,
        )
        self.user = User.objects.create_user(
            username='reviewer', email='r@example.com', password='pass123', is_active=True
        )

    def test_review_post_requires_login(self):
        resp = self.client.post(
            f"/api/commerce/products/{self.product.id}/reviews",
            {"rating": 5, "content": "Nice"}, format='json'
        )
        self.assertEqual(resp.status_code, 401)

    def test_review_create_and_list_updates_product_rating(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/commerce/products/{self.product.id}/reviews",
            {"rating": 4, "title": "Good", "content": "Solid"}, format='json'
        )
        self.assertEqual(resp.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reviews, 1)
        self.assertEqual(float(self.product.rating), 4.0)

        # GET list
        resp = self.client.get(f"/api/commerce/products/{self.product.id}/reviews")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_review_missing_content_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/commerce/products/{self.product.id}/reviews",
            {"rating": 5}, format='json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_all_reviews_and_delete(self):
        review = Review.objects.create(product=self.product, user=self.user, rating=5, content="Excellent")
        resp = self.client.get("/api/commerce/reviews")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(r["id"] == review.id and r.get("productName") == "DSLR" for r in resp.data))

        resp = self.client.delete(f"/api/commerce/reviews/{review.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Review.objects.filter(id=review.id).exists())


class ContactMessageTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Cat")
        self.product = Product.objects.create(name="Cam", price=Decimal("100.00"), category=self.category)
        self.user = User.objects.create_user(
            username='msguser', email='m@example.com', password='pass123', is_active=True
        )

    def test_create_contact_message_anonymous(self):
        payload = {
            "subject": "Question",
            "message": "Is this in stock?",
            "product": self.product.id,
        }
        resp = self.client.post("/api/commerce/messages", payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_create_contact_message_authenticated_links_user(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/commerce/messages",
            {"subject": "Q", "message": "msg"}, format='json'
        )
        self.assertEqual(resp.status_code, 201)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.user_id, self.user.id)

    def test_reply_creates_notification(self):
        msg = ContactMessage.objects.create(user=self.user, subject="Hello", message="Hi")
        resp = self.client.put(
            f"/api/commerce/messages/{msg.id}",
            {"reply": "Hawa, bar"}, format='json'
        )
        self.assertEqual(resp.status_code, 200)
        msg.refresh_from_db()
        self.assertEqual(msg.reply, "Hawa, bar")
        self.assertTrue(msg.is_read)
        self.assertTrue(Notification.objects.filter(user=self.user, type="reply").exists())

    def test_mark_message_read(self):
        msg = ContactMessage.objects.create(subject="S", message="m")
        resp = self.client.put(
            f"/api/commerce/messages/{msg.id}",
            {"is_read": True}, format='json'
        )
        self.assertEqual(resp.status_code, 200)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_delete_message(self):
        msg = ContactMessage.objects.create(subject="S", message="m")
        resp = self.client.delete(f"/api/commerce/messages/{msg.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ContactMessage.objects.filter(id=msg.id).exists())

    def test_message_detail_404(self):
        resp = self.client.put("/api/commerce/messages/99999", {}, format='json')
        self.assertEqual(resp.status_code, 404)


class CommerceOrderViewSetTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Cat")
        self.product = Product.objects.create(name="Cam", price=Decimal("100.00"), category=self.category)
        self.user = User.objects.create_user(
            username='cust', email='c@example.com', password='pass123', is_active=True
        )

    def test_anonymous_can_create_order(self):
        payload = {
            "full_name": "Anon",
            "phone_number": "+99361",
            "items": [{"product": self.product.id, "quantity": 3}],
        }
        resp = self.client.post("/api/commerce/orders", payload, format='json')
        self.assertEqual(resp.status_code, 201)
        order = Order.objects.first()
        self.assertEqual(float(order.total_price), 300.0)
        self.assertEqual(order.items.count(), 1)

    def test_anonymous_cannot_list_orders(self):
        resp = self.client.get("/api/commerce/orders")
        self.assertEqual(resp.status_code, 401)

    def test_authenticated_user_links_to_order(self):
        self.client.force_authenticate(self.user)
        payload = {
            "full_name": "Auth",
            "phone_number": "+99362",
            "items": [{"product": self.product.id, "quantity": 1}],
        }
        resp = self.client.post("/api/commerce/orders", payload, format='json')
        self.assertEqual(resp.status_code, 201)
        order = Order.objects.first()
        self.assertEqual(order.user_id, self.user.id)
