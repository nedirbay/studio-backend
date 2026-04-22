from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from blog.models import BlogMedia, BlogPost
from blog.serializers import BlogPostSerializer
from blog.services import BlogService

blog_service = BlogService()


def _media_dict(media: BlogMedia):
    return {
        "id": media.id,
        "kind": media.kind,
        "url": media.url,
        "created_at": media.created_at.isoformat(),
    }


def _blog_dict(post: BlogPost):
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "main_image": post.main_image,
        "content": post.content,
        "date": post.date.isoformat(),
        "created_at": post.created_at.isoformat(),
        "media": [_media_dict(m) for m in post.media.all()],
    }


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def blogs(request):
    if request.method == "GET":
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 3))
        posts, total = blog_service.get_paginated(page, page_size)
        items = [_blog_dict(p) for p in posts]
        return Response({
            "count": total,
            "results": items,
            "page": page,
            "page_size": page_size
        })
    serializer = BlogPostSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated = serializer.validated_data
    post_data = {k: validated[k] for k in ("title", "main_image", "content", "date") if k in validated}
    media_data = validated.get("media", [])
    post_id = blog_service.create(post_data, media_data)
    return Response({"id": post_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def blog_detail(request, slug: str):
    if request.method == "GET":
        post = blog_service.get_by_slug(slug)
        if not post:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_blog_dict(post))
    if request.method == "PUT":
        serializer = BlogPostSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        post_data = {k: validated[k] for k in ("title", "main_image", "content", "date") if k in validated}
        media_data = validated.get("media") if "media" in validated else None
        updated = blog_service.update(blog_id, post_data, media_data)
        if not updated:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"updated": True})
    deleted = blog_service.delete(blog_id)
    if not deleted:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})
