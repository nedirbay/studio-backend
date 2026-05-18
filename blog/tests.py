import json
from datetime import date

from django.test import Client, TestCase

from blog.models import BlogMedia, BlogPost


class BlogEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = BlogPost.objects.create(title="First", main_image="/img/1.jpg", date=date(2025, 1, 1))
        BlogMedia.objects.create(blog=self.post, kind="image", url="/img/extra.jpg")

    def test_list(self):
        resp = self.client.get("/api/blogs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["count"], 1)
        self.assertIn("media", data["results"][0])

    def test_create_with_media(self):
        payload = {
            "title": "New",
            "main_image": "/img/main2.jpg",
            "date": "2025-02-01",
            "media": [
                {"kind": "image", "url": "/img/a.jpg"},
                {"kind": "video", "url": "https://video.com/v"},
            ],
        }
        resp = self.client.post("/api/blogs", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        new_id = resp.json()["id"]
        post = BlogPost.objects.get(id=new_id)
        self.assertEqual(post.media.count(), 2)

    def test_detail_update_delete(self):
        resp = self.client.get(f"/api/blogs/{self.post.id}")
        self.assertEqual(resp.status_code, 200)
        # update title and replace media with one video
        payload = {"title": "Updated", "media": [{"kind": "video", "url": "vid.mp4"}]}
        resp = self.client.put(
            f"/api/blogs/{self.post.id}", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated")
        self.assertEqual(self.post.media.count(), 1)
        # delete
        resp = self.client.delete(f"/api/blogs/{self.post.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(BlogPost.objects.filter(id=self.post.id).exists())

    def test_detail_not_found(self):
        resp = self.client.get("/api/blogs/99999")
        self.assertEqual(resp.status_code, 404)

    def test_update_not_found(self):
        resp = self.client.put(
            "/api/blogs/99999",
            data=json.dumps({"title": "X"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_not_found(self):
        resp = self.client.delete("/api/blogs/99999")
        self.assertEqual(resp.status_code, 404)

    def test_create_validation_missing_required(self):
        # title and main_image are required
        resp = self.client.post(
            "/api/blogs",
            data=json.dumps({"title": "OnlyTitle"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_pagination(self):
        BlogPost.objects.create(title="P2", main_image="/img/2.jpg", date=date(2025, 1, 2))
        BlogPost.objects.create(title="P3", main_image="/img/3.jpg", date=date(2025, 1, 3))
        BlogPost.objects.create(title="P4", main_image="/img/4.jpg", date=date(2025, 1, 4))

        resp = self.client.get("/api/blogs?page=1&page_size=2")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 4)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 2)
        self.assertEqual(len(data["results"]), 2)

        resp = self.client.get("/api/blogs?page=2&page_size=2")
        self.assertEqual(len(resp.json()["results"]), 2)

    def test_slug_auto_generated(self):
        post = BlogPost.objects.create(title="Hello World", main_image="/x.jpg")
        self.assertEqual(post.slug, "hello-world")
