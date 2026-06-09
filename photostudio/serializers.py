from rest_framework import serializers
from django.conf import settings

from .models import PhotoStudioImage, PhotoStudioVideo


class AbsoluteFileUrlMixin:
    def get_file_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        url = file_field.url
        if request:
            return request.build_absolute_uri(url)
        return url


class PhotoStudioVideoSerializer(AbsoluteFileUrlMixin, serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    hls_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoStudioVideo
        fields = [
            "id",
            "title",
            "description",
            "thumbnail_image",
            "thumbnail_image_url",
            "video",
            "video_url",
            "hls_playlist",
            "hls_url",
            "hls_status",
            "hls_error",
            "create_at",
        ]
        read_only_fields = ["hls_playlist", "hls_status", "hls_error", "create_at"]

    def get_thumbnail_image_url(self, obj):
        return self.get_file_url(obj.thumbnail_image)

    def get_video_url(self, obj):
        return self.get_file_url(obj.video)

    def get_hls_url(self, obj):
        if not obj.hls_playlist:
            return None
        url = f"{settings.MEDIA_URL}{obj.hls_playlist}"
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url


class PhotoStudioImageSerializer(AbsoluteFileUrlMixin, serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoStudioImage
        fields = [
            "id",
            "title",
            "description",
            "thumbnail_image",
            "thumbnail_image_url",
            "image",
            "image_url",
            "create_at",
        ]
        read_only_fields = ["create_at"]

    def get_thumbnail_image_url(self, obj):
        return self.get_file_url(obj.thumbnail_image)

    def get_image_url(self, obj):
        return self.get_file_url(obj.image)
