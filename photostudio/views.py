from rest_framework import permissions, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser

from .models import PhotoStudioImage, PhotoStudioVideo
from .serializers import PhotoStudioImageSerializer, PhotoStudioVideoSerializer
from .services import generate_hls_for_video


class PhotoStudioMediaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class PhotoStudioMediaMixin:
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = PhotoStudioMediaPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset


class PhotoStudioVideoViewSet(PhotoStudioMediaMixin, viewsets.ModelViewSet):
    queryset = PhotoStudioVideo.objects.all()
    serializer_class = PhotoStudioVideoSerializer

    def perform_create(self, serializer):
        video = serializer.save()
        generate_hls_for_video(video)


class PhotoStudioImageViewSet(PhotoStudioMediaMixin, viewsets.ModelViewSet):
    queryset = PhotoStudioImage.objects.all()
    serializer_class = PhotoStudioImageSerializer
