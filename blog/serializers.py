from rest_framework import serializers

from blog.models import BlogMedia, BlogPost


class BlogMediaSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["image", "video"])
    url = serializers.CharField(max_length=255)


class BlogPostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    main_image = serializers.CharField(max_length=255)
    date = serializers.DateField(required=False, allow_null=True)
    media = BlogMediaSerializer(many=True, required=False, allow_null=True)

    def create(self, validated_data):
        media = validated_data.pop("media", [])
        post = BlogPost.objects.create(**validated_data)
        for item in media or []:
            BlogMedia.objects.create(blog=post, **item)
        return post

    def update(self, instance, validated_data):
        media = validated_data.pop("media", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if media is not None:
            instance.media.all().delete()
            for item in media or []:
                BlogMedia.objects.create(blog=instance, **item)
        return instance
