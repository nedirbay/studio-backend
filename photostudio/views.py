from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F

from .models import (
    PhotoCategory,
    PhotoCollection,
    PhotoBlog,
    PhotoReel,
    PhotoReelLike,
    PhotoReelComment,
    PhotoReelShare,
)
from .serializers import (
    PhotoCategorySerializer,
    PhotoCollectionSerializer,
    PhotoBlogSerializer,
    PhotoReelSerializer,
    PhotoReelCommentSerializer,
)


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


class PhotoCollectionViewSet(viewsets.ModelViewSet):
    queryset = PhotoCollection.objects.filter(is_published=True).select_related('category').prefetch_related(
        'reels__category', 'reels__collection', 'reels__author', 'reels__tags', 'reels__likes', 'reels__comments', 'reels__shares'
    )
    serializer_class = PhotoCollectionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        kind = self.request.query_params.get('kind')
        category_id = self.request.query_params.get('category')
        if kind:
            queryset = queryset.filter(kind=kind)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class PhotoReelViewSet(viewsets.ModelViewSet):
    queryset = PhotoReel.objects.filter(is_published=True).select_related('category', 'collection', 'author').prefetch_related('tags', 'likes', 'comments', 'shares')
    serializer_class = PhotoReelSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get('category')
        kind = self.request.query_params.get('kind')
        collection_id = self.request.query_params.get('collection')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if kind:
            qs = qs.filter(kind=kind)
        if collection_id:
            qs = qs.filter(collection_id=collection_id)
        return qs

    def perform_create(self, serializer):
        author = self.request.user if self.request.user.is_authenticated else None
        serializer.save(author=author)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def view(self, request, pk=None):
        PhotoReel.objects.filter(pk=pk).update(views=F('views') + 1)
        reel = self.get_object()
        return Response({'views': reel.views})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        reel = self.get_object()
        like, created = PhotoReelLike.objects.get_or_create(reel=reel, user=request.user)
        if not created:
            like.delete()
        count = PhotoReelLike.objects.filter(reel=reel).count()
        return Response({'liked': created, 'likes_count': count})

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.AllowAny])
    def comments(self, request, pk=None):
        reel = self.get_object()
        if request.method == 'GET':
            comments = reel.comments.filter(parent__isnull=True).select_related('user').order_by('-created_at')
            serializer = PhotoReelCommentSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response({'detail': 'Awtorizasiýa hökmany'}, status=status.HTTP_401_UNAUTHORIZED)

        text = (request.data.get('text') or '').strip()
        parent_id = request.data.get('parent')
        if not text:
            return Response({'detail': 'Teswir boş bolup bilmez'}, status=status.HTTP_400_BAD_REQUEST)
        comment = PhotoReelComment.objects.create(
            reel=reel,
            user=request.user,
            text=text,
            parent_id=parent_id,
        )
        serializer = PhotoReelCommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def share(self, request, pk=None):
        reel = self.get_object()
        channel = request.data.get('channel', '')
        user = request.user if request.user.is_authenticated else None
        PhotoReelShare.objects.create(reel=reel, user=user, channel=channel)
        count = PhotoReelShare.objects.filter(reel=reel).count()
        return Response({'shares_count': count})


class PhotoReelCommentViewSet(viewsets.ModelViewSet):
    queryset = PhotoReelComment.objects.all().select_related('user', 'reel')
    serializer_class = PhotoReelCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        reel_id = self.request.query_params.get('reel')
        if reel_id:
            qs = qs.filter(reel_id=reel_id)
        return qs
