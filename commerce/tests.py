import json
from decimal import Decimal

from django.test import Client, TestCase

from commerce.models import Category, Product, ProductMedia


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
        resp = self.client.get("/api/categories")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()), 1)

        resp = self.client.post("/api/categories", data=json.dumps({"name": "Lenses"}), content_type="application/json")
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
        resp = self.client.post("/api/products", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        new_id = resp.json()["id"]
        prod = Product.objects.get(id=new_id)
        self.assertEqual(prod.media.count(), 2)

    def test_product_detail_update_delete(self):
        resp = self.client.get(f"/api/products/{self.product.id}")
        self.assertEqual(resp.status_code, 200)
        # update instock and replace media with one video
        payload = {"instock": False, "media": [{"kind": "video", "url": "vid.mp4"}]}
        resp = self.client.put(
            f"/api/products/{self.product.id}", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.instock)
        self.assertEqual(self.product.media.count(), 1)
        # delete
        resp = self.client.delete(f"/api/products/{self.product.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())
