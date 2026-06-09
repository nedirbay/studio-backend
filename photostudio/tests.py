from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PhotoStudioImage, PhotoStudioVideo


class PhotoStudioTests(APITestCase):
    def test_upload_and_list_video(self):
        response = self.client.post(
            "/api/photostudio/videos/",
            {
                "title": "Wedding Video",
                "description": "Best moments",
                "thumbnail_image": SimpleUploadedFile("thumb.jpg", b"thumb", content_type="image/jpeg"),
                "video": SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PhotoStudioVideo.objects.count(), 1)

        list_response = self.client.get("/api/photostudio/videos/?search=Wedding")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["title"], "Wedding Video")

    def test_upload_and_list_image(self):
        response = self.client.post(
            "/api/photostudio/images/",
            {
                "title": "Studio Image",
                "description": "Portrait session",
                "thumbnail_image": SimpleUploadedFile("thumb.jpg", b"thumb", content_type="image/jpeg"),
                "image": SimpleUploadedFile("image.jpg", b"image", content_type="image/jpeg"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PhotoStudioImage.objects.count(), 1)

        list_response = self.client.get("/api/photostudio/images/?page=1&page_size=10&search=Studio")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["title"], "Studio Image")
