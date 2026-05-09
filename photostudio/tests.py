from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import PhotoCategory, PhotoBlog, PhotoMedia

class PhotoStudioTests(APITestCase):
    def setUp(self):
        self.category = PhotoCategory.objects.create(name="Wedding", slug="wedding")
        self.blog = PhotoBlog.objects.create(
            category=self.category,
            title="Cool Wedding",
            description="Best wedding ever"
        )
        self.media = PhotoMedia.objects.create(
            blog=self.blog,
            kind="image",
            url="http://example.com/img.jpg"
        )

    def test_list_categories(self):
        url = '/api/photostudio/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_blogs(self):
        url = '/api/photostudio/blogs/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Cool Wedding")
        self.assertEqual(len(response.data[0]['media']), 1)

    def test_filter_blogs_by_category(self):
        url = f'/api/photostudio/blogs/?category={self.category.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
