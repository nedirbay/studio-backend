from rest_framework import viewsets, permissions
from .models import PhotoCategory, PhotoBlog
from .serializers import PhotoCategorySerializer, PhotoBlogSerializer

class PhotoCategoryViewSet(viewsets.ModelViewSet):
    queryset = PhotoCategory.objects.all().order_by('name')
    serializer_class = PhotoCategorySerializer
    permission_classes = [permissions.AllowAny]

class PhotoBlogViewSet(viewsets.ModelViewSet):
    queryset = PhotoBlog.objects.all().order_by('-date')
    serializer_class = PhotoBlogSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
