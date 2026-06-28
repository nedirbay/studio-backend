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

    def test_brand_create_update_delete(self):
        # Create
        payload = {"name": "Sony", "slug": "sony", "logo_url": "/img/sony.png"}
        resp = self.client.post("/api/commerce/brands", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        brand_id = resp.json()["id"]
        self.assertTrue(Brand.objects.filter(id=brand_id).exists())

        # Update
        update_payload = {"name": "Sony Updated", "logo_url": "/img/sony_new.png"}
        resp = self.client.put(f"/api/commerce/brands/{brand_id}", data=json.dumps(update_payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        brand = Brand.objects.get(id=brand_id)
        self.assertEqual(brand.name, "Sony Updated")
        self.assertEqual(brand.logo_url, "/img/sony_new.png")

        # Delete
        resp = self.client.delete(f"/api/commerce/brands/{brand_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Brand.objects.filter(id=brand_id).exists())

    def test_category_and_brand_slug_auto_generation_and_collision(self):
        # Test Category slug auto generation and collision
        cat1 = Category.objects.create(name="Smart Phones")
        cat2 = Category.objects.create(name="Smart Phones")
        self.assertEqual(cat1.slug, "smart-phones")
        self.assertEqual(cat2.slug, "smart-phones-1")

        # Test Brand slug auto generation and collision
        brand1 = Brand.objects.create(name="Sony Alpha")
        brand2 = Brand.objects.create(name="Sony Alpha")
        self.assertEqual(brand1.slug, "sony-alpha")
        self.assertEqual(brand2.slug, "sony-alpha-1")


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
        self.assertTrue(any(r["id"] == review.id and r.get("productName") == "DSLR" for r in resp.data["results"]))

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


class ProductFormFieldTests(TestCase):
    """
    Verify that every field in the ProductDialog form is correctly
    mapped to the backend Product model through the API.

    Field mapping (frontend → backend):
      name           → name
      price          → price
      originalPrice  → original_price
      inStock        → instock
      brand          → marka
      category       → category (FK, sent as ID)
      badge          → badge
      description    → description
      features       → features  (JSONField list)
      specifications → specifications (JSONField dict)
      media          → ProductMedia (related set, kind + url)
    """

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Kamera")
        self.brand = Brand.objects.create(name="Sony", slug="sony")

    def _full_payload(self, **overrides):
        """Return a complete product payload with all form fields."""
        base = {
            "name": "Sony A7 IV",
            "price": "1299.99",
            "original_price": "1499.99",
            "instock": True,
            "marka": "Sony",
            "badge": "new",
            "description": "Full-frame mirrorless camera",
            "features": ["33MP sensor", "10fps burst"],
            "specifications": {"weight": "659g", "sensor": "full-frame"},
            "category": self.category.id,
            "media": [
                {"kind": "image", "url": "/media/products/a7iv.jpg"},
                {"kind": "video", "url": "https://youtube.com/watch?v=abc"},
            ],
        }
        base.update(overrides)
        return base

    def test_create_with_all_form_fields(self):
        """POST with full form payload → all fields saved to database."""
        payload = self._full_payload()
        resp = self.client.post(
            "/api/commerce/products",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        prod = Product.objects.get(id=resp.json()["id"])

        self.assertEqual(prod.name, "Sony A7 IV")
        self.assertEqual(float(prod.price), 1299.99)
        self.assertEqual(float(prod.original_price), 1499.99)
        self.assertTrue(prod.instock)
        self.assertEqual(prod.marka, "Sony")
        self.assertEqual(prod.badge, "new")
        self.assertEqual(prod.description, "Full-frame mirrorless camera")
        self.assertEqual(prod.features, ["33MP sensor", "10fps burst"])
        self.assertEqual(prod.specifications, {"weight": "659g", "sensor": "full-frame"})
        self.assertEqual(prod.category_id, self.category.id)
        self.assertEqual(prod.media.count(), 2)
        media_kinds = set(prod.media.values_list("kind", flat=True))
        self.assertIn("image", media_kinds)
        self.assertIn("video", media_kinds)

    def test_api_response_contains_expected_keys(self):
        """GET response includes all keys the frontend expects to render."""
        product = Product.objects.create(
            name="Test Product",
            price=Decimal("100.00"),
            original_price=Decimal("150.00"),
            instock=False,
            marka="Canon",
            badge="sale",
            description="Test",
            features=["f1", "f2"],
            specifications={"k": "v"},
            category=self.category,
        )
        resp = self.client.get(f"/api/commerce/products/{product.id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Keys the frontend reads from _product_dict()
        for key in ["id", "name", "price", "original_price", "instock",
                    "marka", "badge", "description", "features",
                    "specifications", "rating", "reviews",
                    "category_id", "category_name", "media", "created_at"]:
            self.assertIn(key, data, msg=f"Missing key in API response: {key}")

        self.assertEqual(data["name"], "Test Product")
        self.assertEqual(float(data["price"]), 100.0)
        self.assertEqual(float(data["original_price"]), 150.0)
        self.assertFalse(data["instock"])
        self.assertEqual(data["marka"], "Canon")
        self.assertEqual(data["badge"], "sale")
        self.assertEqual(data["features"], ["f1", "f2"])
        self.assertEqual(data["specifications"], {"k": "v"})
        self.assertEqual(data["category_name"], "Kamera")

    def test_update_all_optional_fields(self):
        """PUT with changed values updates all optional fields in the model."""
        product = Product.objects.create(
            name="Old Name",
            price=Decimal("100.00"),
            category=self.category,
        )
        update_payload = {
            "name": "New Name",
            "price": "200.00",
            "original_price": "250.00",
            "instock": False,
            "marka": "Nikon",
            "badge": "hot",
            "description": "Updated description",
            "features": ["updated feature"],
            "specifications": {"size": "large"},
            "category": self.category.id,
            "media": [{"kind": "image", "url": "/media/products/new.jpg"}],
        }
        resp = self.client.put(
            f"/api/commerce/products/{product.id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        product.refresh_from_db()

        self.assertEqual(product.name, "New Name")
        self.assertEqual(float(product.price), 200.0)
        self.assertEqual(float(product.original_price), 250.0)
        self.assertFalse(product.instock)
        self.assertEqual(product.marka, "Nikon")
        self.assertEqual(product.badge, "hot")
        self.assertEqual(product.description, "Updated description")
        self.assertEqual(product.features, ["updated feature"])
        self.assertEqual(product.specifications, {"size": "large"})
        self.assertEqual(product.media.count(), 1)

    def test_delete_product(self):
        """DELETE removes the product and its media."""
        product = Product.objects.create(
            name="To Delete", price=Decimal("10.00"), category=self.category
        )
        ProductMedia.objects.create(product=product, kind="image", url="/img/del.jpg")

        resp = self.client.delete(f"/api/commerce/products/{product.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Product.objects.filter(id=product.id).exists())
        self.assertFalse(ProductMedia.objects.filter(product_id=product.id).exists())

    def test_create_missing_required_fields_returns_400(self):
        """POST without required fields (name, price, category) returns 400."""
        resp = self.client.post(
            "/api/commerce/products",
            data=json.dumps({"name": "NoPrice"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_with_invalid_category_returns_400(self):
        """POST with non-existent category ID returns 400."""
        payload = self._full_payload(category=99999)
        resp = self.client.post(
            "/api/commerce/products",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_media_sync_on_update_replaces_old_media(self):
        """PUT with new media list replaces all existing media (not appends)."""
        product = Product.objects.create(
            name="Media Test", price=Decimal("50.00"), category=self.category
        )
        ProductMedia.objects.create(product=product, kind="image", url="/img/old1.jpg")
        ProductMedia.objects.create(product=product, kind="image", url="/img/old2.jpg")
        self.assertEqual(product.media.count(), 2)

        resp = self.client.put(
            f"/api/commerce/products/{product.id}",
            data=json.dumps({
                "category": self.category.id,
                "media": [{"kind": "image", "url": "/img/new.jpg"}],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(product.media.count(), 1)
        self.assertEqual(product.media.first().url, "/img/new.jpg")
