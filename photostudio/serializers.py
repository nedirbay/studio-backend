from rest_framework import serializers
from .models import (
    PhotoCategory,
    PhotoCollection,
    PhotoBlog,
    PhotoMedia,
    PhotoReel,
    PhotoReelTag,
    PhotoReelLike,
    PhotoReelComment,
    PhotoReelShare,
)


class PhotoMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoMedia
        fields = ['id', 'kind', 'url', 'created_at']


class PhotoBlogSerializer(serializers.ModelSerializer):
    media = PhotoMediaSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = PhotoBlog
        fields = ['id', 'category', 'category_name', 'title', 'description', 'date', 'media', 'created_at']


class PhotoCategorySerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(source='blogs.count', read_only=True)
    reels_count = serializers.IntegerField(source='reels.count', read_only=True)
    collections_count = serializers.IntegerField(source='collections.count', read_only=True)

    class Meta:
        model = PhotoCategory
        fields = ['id', 'name', 'slug', 'blog_count', 'reels_count', 'collections_count', 'created_at']


class PhotoReelTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoReelTag
        fields = ['id', 'name']


class PhotoReelCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PhotoReelComment
        fields = ['id', 'reel', 'user', 'user_name', 'user_avatar', 'text', 'parent', 'replies', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_user_name(self, obj):
        if obj.user:
            return getattr(obj.user, 'username', None) or getattr(obj.user, 'email', None) or 'Ulanyjy'
        return 'Ulanyjy'

    def get_user_avatar(self, obj):
        if obj.user and hasattr(obj.user, 'avatar') and obj.user.avatar:
            return obj.user.avatar
        return None

    def get_replies(self, obj):
        qs = obj.replies.all().order_by('created_at')[:20]
        return PhotoReelCommentSerializer(qs, many=True, context=self.context).data


class PhotoReelSerializer(serializers.ModelSerializer):
    tags = PhotoReelTagSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    collection_id = serializers.IntegerField(source='collection.id', read_only=True)
    collection_title = serializers.CharField(source='collection.title', read_only=True)
    author_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    shares_count = serializers.IntegerField(read_only=True)
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = PhotoReel
        fields = [
            'id', 'category', 'category_name', 'collection', 'collection_id', 'collection_title',
            'author', 'author_name', 'author_avatar',
            'title', 'description', 'kind', 'media_url', 'thumbnail_url', 'stream_url',
            'duration', 'music_title', 'views', 'is_published',
            'tags', 'likes_count', 'comments_count', 'shares_count', 'liked_by_me',
            'created_at',
        ]
        read_only_fields = ['views', 'created_at', 'author']

    def get_author_name(self, obj):
        if obj.author:
            return getattr(obj.author, 'username', None) or getattr(obj.author, 'email', None) or 'Studio'
        return 'Doganlar Studio'

    def get_author_avatar(self, obj):
        if obj.author and hasattr(obj.author, 'avatar') and obj.author.avatar:
            return obj.author.avatar
        return None

    def get_liked_by_me(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return PhotoReelLike.objects.filter(reel=obj, user=request.user).exists()


class PhotoReelShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoReelShare
        fields = ['id', 'reel', 'user', 'channel', 'created_at']
        read_only_fields = ['user', 'created_at']


class PhotoCollectionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = PhotoCollection
        fields = [
            'id', 'category', 'category_name', 'title', 'description', 'kind',
            'cover_url', 'is_published', 'sort_order', 'items_count', 'items', 'created_at',
        ]

    def get_items(self, obj):
        queryset = obj.reels.filter(is_published=True).select_related('category', 'collection', 'author').prefetch_related('tags', 'likes', 'comments', 'shares')
        return PhotoReelSerializer(queryset, many=True, context=self.context).data
