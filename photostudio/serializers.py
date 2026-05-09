from rest_framework import serializers
from .models import PhotoCategory, PhotoBlog, PhotoMedia

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

    class Meta:
        model = PhotoCategory
        fields = ['id', 'name', 'slug', 'blog_count', 'created_at']
