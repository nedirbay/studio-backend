from rest_framework.test import APITestCase
from rest_framework import status
from identity.models import Role, User

from .models import PhotoCategory, PhotoCollection, PhotoBlog, PhotoMedia, PhotoReel, PhotoReelComment, PhotoReelTag

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
        role = Role.objects.create(name="studio-user")
        self.user = User.objects.create_user(
            username="studio-user",
            email="studio@example.com",
            password="password123",
            role=role,
            is_active=True,
        )
        self.collection = PhotoCollection.objects.create(
            category=self.category,
            title="Wedding Videos",
            description="Grouped wedding videos",
            kind="video",
            cover_url="http://example.com/cover.jpg",
        )
        self.reel = PhotoReel.objects.create(
            category=self.category,
            collection=self.collection,
            author=self.user,
            title="Wedding Reel",
            description="Best moments",
            kind="video",
            media_url="http://example.com/reel.mp4",
            thumbnail_url="http://example.com/thumb.jpg",
            duration=18,
            is_published=True,
        )
        PhotoReelTag.objects.create(reel=self.reel, name="wedding")
        self.comment = PhotoReelComment.objects.create(reel=self.reel, user=self.user, text="Nice shoot")
        PhotoReel.objects.create(
            category=self.category,
            collection=self.collection,
            author=self.user,
            title="Wedding Reel 2",
            description="Second clip",
            kind="video",
            media_url="http://example.com/reel-2.mp4",
            thumbnail_url="http://example.com/thumb-2.jpg",
            duration=20,
            is_published=True,
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

    def test_reels_list_includes_tags_and_counts(self):
        response = self.client.get('/api/photostudio/reels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        titles = {item['title'] for item in response.data}
        self.assertIn("Wedding Reel", titles)
        detail = next(item for item in response.data if item['title'] == "Wedding Reel")
        self.assertEqual(detail['tags'][0]['name'], "wedding")
        self.assertEqual(detail['comments_count'], 1)

    def test_collections_list_includes_nested_items(self):
        response = self.client.get('/api/photostudio/collections/?kind=video')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Wedding Videos")
        self.assertEqual(response.data[0]['items_count'], 2)
        self.assertEqual(len(response.data[0]['items']), 2)

    def test_reel_like_toggle_and_comments(self):
        self.client.force_authenticate(self.user)

        like_response = self.client.post(f'/api/photostudio/reels/{self.reel.id}/like/')
        self.assertEqual(like_response.status_code, status.HTTP_200_OK)
        self.assertTrue(like_response.data['liked'])

        unlike_response = self.client.post(f'/api/photostudio/reels/{self.reel.id}/like/')
        self.assertEqual(unlike_response.status_code, status.HTTP_200_OK)
        self.assertFalse(unlike_response.data['liked'])

        comment_response = self.client.post(
            f'/api/photostudio/reels/{self.reel.id}/comments/',
            {'text': 'Another comment'},
            format='json'
        )
        self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)

        list_response = self.client.get(f'/api/photostudio/reels/{self.reel.id}/comments/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 2)

    def test_reel_like_requires_authentication(self):
        response = self.client.post(f'/api/photostudio/reels/{self.reel.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reel_comment_post_requires_authentication(self):
        response = self.client.post(
            f'/api/photostudio/reels/{self.reel.id}/comments/',
            {'text': 'no-auth'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reel_empty_comment_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            f'/api/photostudio/reels/{self.reel.id}/comments/',
            {'text': '   '},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reel_view_increments(self):
        before = self.reel.views
        response = self.client.post(f'/api/photostudio/reels/{self.reel.id}/view/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['views'], before + 1)
        self.reel.refresh_from_db()
        self.assertEqual(self.reel.views, before + 1)

    def test_reel_share_endpoint(self):
        response = self.client.post(
            f'/api/photostudio/reels/{self.reel.id}/share/',
            {'channel': 'whatsapp'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shares_count'], 1)

    def test_reel_filter_by_collection(self):
        other = PhotoCollection.objects.create(
            category=self.category, title="Other", kind="video"
        )
        PhotoReel.objects.create(
            category=self.category,
            collection=other,
            title="Other Reel",
            kind="video",
            media_url="http://example.com/o.mp4",
            is_published=True,
        )
        response = self.client.get(f'/api/photostudio/reels/?collection={self.collection.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item['collection'], self.collection.id)

    def test_reel_filter_by_kind(self):
        PhotoReel.objects.create(
            category=self.category,
            title="Image Reel",
            kind="image",
            media_url="http://example.com/img.jpg",
            is_published=True,
        )
        response = self.client.get('/api/photostudio/reels/?kind=image')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item['kind'], 'image')

    def test_unpublished_reels_excluded(self):
        PhotoReel.objects.create(
            category=self.category,
            title="Hidden",
            kind="video",
            media_url="http://example.com/h.mp4",
            is_published=False,
        )
        response = self.client.get('/api/photostudio/reels/')
        titles = {r['title'] for r in response.data}
        self.assertNotIn("Hidden", titles)

    def test_comment_reply_relationship(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            f'/api/photostudio/reels/{self.reel.id}/comments/',
            {'text': 'Reply!', 'parent': self.comment.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reply = PhotoReelComment.objects.get(id=response.data['id'])
        self.assertEqual(reply.parent_id, self.comment.id)

    def test_collection_filter_by_kind(self):
        PhotoCollection.objects.create(category=self.category, title="Img Coll", kind="image")
        response = self.client.get('/api/photostudio/collections/?kind=image')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item['kind'], 'image')

    def test_unpublished_collection_hidden(self):
        PhotoCollection.objects.create(
            category=self.category, title="Hidden", kind="video", is_published=False
        )
        response = self.client.get('/api/photostudio/collections/')
        titles = {c['title'] for c in response.data}
        self.assertNotIn("Hidden", titles)
