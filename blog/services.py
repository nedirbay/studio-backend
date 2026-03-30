from typing import Optional
from django.db import transaction

from blog.models import BlogMedia, BlogPost


class BlogService:
    def get_all(self):
        return list(BlogPost.objects.all().order_by('-date', '-created_at').prefetch_related('media'))

    def get_by_id(self, blog_id: int) -> Optional[BlogPost]:
        return BlogPost.objects.filter(id=blog_id).prefetch_related('media').first()

    @transaction.atomic
    def create(self, post_data: dict, media_data: list) -> int:
        post = BlogPost.objects.create(**post_data)
        self._sync_media(post, media_data)
        return post.id

    @transaction.atomic
    def update(self, blog_id: int, post_data: dict, media_data: list) -> bool:
        if not BlogPost.objects.filter(id=blog_id).exists():
            return False
        BlogPost.objects.filter(id=blog_id).update(**post_data)
        post = BlogPost.objects.get(id=blog_id)
        self._sync_media(post, media_data)
        return True

    def delete(self, blog_id: int) -> bool:
        deleted, _ = BlogPost.objects.filter(id=blog_id).delete()
        return deleted > 0

    def _sync_media(self, post: BlogPost, media_data: list):
        # replace existing media with provided list
        if media_data is None:
            return
        BlogMedia.objects.filter(blog=post).delete()
        objs = []
        for item in media_data:
            kind = item.get('kind')
            url = item.get('url')
            if kind not in {'image', 'video'} or not url:
                continue
            objs.append(BlogMedia(blog=post, kind=kind, url=url))
        if objs:
            BlogMedia.objects.bulk_create(objs)
