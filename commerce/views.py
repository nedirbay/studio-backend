from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from commerce.models import Category, Product, ProductMedia, Brand, Review
from commerce.serializers import CategorySerializer, ProductSerializer, BrandSerializer
from commerce.services import CategoryService, ProductService

from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import FileSystemStorage
from django.conf import settings

category_service = CategoryService()
product_service = ProductService()

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_image(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    fs = FileSystemStorage()
    filename = fs.save(f"products/{file.name}", file)
    file_url = f"{settings.MEDIA_URL}{filename}"
    
    return Response({'url': file_url}, status=status.HTTP_201_CREATED)


def _category_dict(cat: Category):
    return {
        "id": cat.id, 
        "name": cat.name, 
        "slug": cat.slug,
        "icon": cat.icon,
        "count": cat.count,
        "created_at": cat.created_at.isoformat()
    }

def _brand_dict(brand: Brand):
    return {
        "id": brand.id,
        "name": brand.name,
        "slug": brand.slug,
        "logo_url": brand.logo_url,
        "created_at": brand.created_at.isoformat()
    }


def _media_dict(media: ProductMedia, request=None):
    url = media.url
    if url and not (url.startswith('http://') or url.startswith('https://')):
        if request:
            url = request.build_absolute_uri(url)
        else:
            url = f"http://127.0.0.1:8000{url}" if url.startswith('/') else f"http://127.0.0.1:8000/{url}"
    return {"id": media.id, "kind": media.kind, "url": url, "created_at": media.created_at.isoformat()}

def _product_list_dict(prod: Product, request=None):
    """Card üçin ýeňil maglumat — artykmaç description/features/specifications ýok"""
    first_media = prod.media.first()
    image_url = None
    if first_media:
        url = first_media.url
        if url.startswith('http://') or url.startswith('https://'):
            image_url = url
        elif request:
            image_url = request.build_absolute_uri(url)
        else:
            image_url = f"http://127.0.0.1:8000{url}" if url.startswith('/') else f"http://127.0.0.1:8000/{url}"
    return {
        "id": prod.id,
        "slug": prod.slug,
        "name": prod.name,
        "price": float(prod.price),
        "original_price": float(prod.original_price) if prod.original_price else None,
        "instock": prod.instock,
        "rating": float(prod.rating),
        "reviews": prod.reviews,
        "badge": prod.badge,
        "marka": prod.marka,
        "category_id": prod.category_id,
        "category_name": prod.category.name if prod.category else None,
        "image": image_url,
    }

def _product_dict(prod: Product, request=None):
    """Detail sahypa üçin doly maglumat"""
    return {
        "id": prod.id,
        "slug": prod.slug,
        "name": prod.name,
        "price": float(prod.price),
        "original_price": float(prod.original_price) if prod.original_price else None,
        "instock": prod.instock,
        "rating": float(prod.rating),
        "reviews": prod.reviews,
        "badge": prod.badge,
        "description": prod.description,
        "features": prod.features,
        "specifications": prod.specifications,
        "created_at": prod.created_at.isoformat(),
        "marka": prod.marka,
        "category_id": prod.category_id,
        "category_name": prod.category.name if prod.category else None,
        "media": [_media_dict(m, request) for m in prod.media.all()],
    }

def _review_dict(review: Review):
    return {
        "id": review.id,
        "user_id": review.user_id,
        "userName": review.user.username,
        "rating": review.rating,
        "title": review.title,
        "content": review.content,
        "createdAt": review.created_at.isoformat(),
        "helpful": 0,
        "is_read": review.is_read
    }


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def categories(request):
    if request.method == "GET":
        return Response([_category_dict(c) for c in category_service.get_all()])
    serializer = CategorySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated = serializer.validated_data
    slug = validated.get("slug")
    if slug and Category.objects.filter(slug=slug).exists():
        return Response({"slug": ["This slug is already in use."]}, status=status.HTTP_400_BAD_REQUEST)
    cat = Category.objects.create(
        name=validated["name"],
        slug=validated.get("slug"),
        icon=validated.get("icon")
    )
    return Response(_category_dict(cat), status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def category_detail(request, category_id: int):
    try:
        cat = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == "GET":
        return Response(_category_dict(cat))
        
    elif request.method == "PUT":
        serializer = CategorySerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        if "name" in validated:
            cat.name = validated["name"]
        if "slug" in validated:
            slug = validated["slug"]
            if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
                return Response({"slug": ["This slug is already in use."]}, status=status.HTTP_400_BAD_REQUEST)
            cat.slug = slug
        if "icon" in validated:
            cat.icon = validated["icon"]
        cat.save()
        return Response(_category_dict(cat))
        
    elif request.method == "DELETE":
        cat.delete()
        return Response({"deleted": True})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def products(request):
    if request.method == "GET":
        return Response([_product_list_dict(p, request) for p in product_service.get_all()])
    serializer = ProductSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated = serializer.validated_data
    product_data = {
        "name": validated["name"],
        "price": validated["price"],
        "instock": validated.get("instock", True),
        "marka": validated.get("marka"),
        "category_id": validated["category"],
        "original_price": validated.get("original_price"),
        "badge": validated.get("badge"),
        "description": validated.get("description"),
        "features": validated.get("features", []),
        "specifications": validated.get("specifications", {}),
    }
    media_data = validated.get("media", [])
    new_id = product_service.create(product_data, media_data)
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def product_detail(request, product_id: int):
    if request.method == "GET":
        prod = product_service.get_by_id(product_id)
        if not prod:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_product_dict(prod, request))
    if request.method == "PUT":
        serializer = ProductSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        product_data = {}
        for field in ["name", "price", "instock", "marka", "original_price",
                      "badge", "description", "features", "specifications"]:
            if field in validated:
                product_data[field] = validated[field]
        if "category" in validated:
            product_data["category_id"] = validated["category"]
        media_data = validated.get("media") if "media" in validated else None
        updated = product_service.update(product_id, product_data, media_data)
        if not updated:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"updated": True})
    deleted = product_service.delete(product_id)
    if not deleted:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail_by_slug(request, slug: str):
    prod = product_service.get_by_slug(slug)
    if not prod:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(_product_dict(prod, request))


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def brands(request):
    if request.method == "GET":
        return Response([_brand_dict(b) for b in Brand.objects.all().order_by('name')])
    serializer = BrandSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated = serializer.validated_data
    slug = validated.get("slug")
    if slug and Brand.objects.filter(slug=slug).exists():
        return Response({"slug": ["This slug is already in use."]}, status=status.HTTP_400_BAD_REQUEST)
    brand = Brand.objects.create(
        name=validated["name"],
        slug=validated.get("slug"),
        logo_url=validated.get("logo_url")
    )
    return Response(_brand_dict(brand), status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def brand_detail(request, brand_id: int):
    try:
        brand = Brand.objects.get(id=brand_id)
    except Brand.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == "GET":
        return Response(_brand_dict(brand))
        
    elif request.method == "PUT":
        serializer = BrandSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        if "name" in validated:
            brand.name = validated["name"]
        if "slug" in validated:
            slug = validated["slug"]
            if Brand.objects.filter(slug=slug).exclude(id=brand_id).exists():
                return Response({"slug": ["This slug is already in use."]}, status=status.HTTP_400_BAD_REQUEST)
            brand.slug = slug
        if "logo_url" in validated:
            brand.logo_url = validated["logo_url"]
        brand.save()
        return Response(_brand_dict(brand))
        
    elif request.method == "DELETE":
        brand.delete()
        return Response({"deleted": True})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def product_reviews(request, product_id: int):
    if request.method == "GET":
        reviews = Review.objects.filter(product_id=product_id).select_related('user').order_by('-created_at')
        return Response([_review_dict(r) for r in reviews])
    
    # POST - Add Review
    if not request.user.is_authenticated:
        return Response({"error": "Login gerek"}, status=status.HTTP_401_UNAUTHORIZED)
    
    data = request.data
    rating = data.get("rating", 5)
    title = data.get("title", "")
    content = data.get("content")

    if not content:
        return Response({"error": "Teswir ýazyň"}, status=status.HTTP_400_BAD_REQUEST)

    review = Review.objects.create(
        product_id=product_id,
        user=request.user,
        rating=rating,
        title=title,
        content=content
    )
    
    # Broadcast event
    try:
        from management.ws_utils import broadcast_order_event
        d = _review_dict(review)
        d['productName'] = review.product.name if review.product else 'Näbelli haryt'
        d['productId'] = review.product_id
        broadcast_order_event("review_created", {"review": d})
    except Exception as e:
        print("Failed to broadcast review_created:", e)
        
    return Response(_review_dict(review), status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([AllowAny])
def all_reviews(request):
    reviews = Review.objects.all().select_related('user', 'product').order_by('-created_at')
    
    # Search filter
    search = request.query_params.get('search')
    if search:
        from django.db.models import Q
        reviews = reviews.filter(
            Q(user__username__icontains=search) | 
            Q(product__name__icontains=search) | 
            Q(content__icontains=search)
        )
        
    # Rating filter
    rating = request.query_params.get('rating')
    if rating:
        reviews = reviews.filter(rating=rating)
        
    # Page pagination
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginated_reviews = paginator.paginate_queryset(reviews, request)
    
    result = []
    for r in paginated_reviews:
        d = _review_dict(r)
        d['productName'] = r.product.name if r.product else 'Näbelli haryt'
        d['productId'] = r.product_id
        result.append(d)
        
    return paginator.get_paginated_response(result)

@api_view(["DELETE", "PUT"])
@permission_classes([AllowAny])
def review_detail(request, review_id: int):
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == "DELETE":
        review_id = review.id
        review.delete()
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("review_deleted", {"review_id": review_id})
        except Exception as e:
            print("Failed to broadcast review_deleted:", e)
        return Response({"deleted": True})
        
    elif request.method == "PUT":
        if "is_read" in request.data:
            review.is_read = request.data["is_read"]
            review.save()
            
        d = _review_dict(review)
        d['productName'] = review.product.name if review.product else 'Näbelli haryt'
        d['productId'] = review.product_id
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("review_updated", {"review": d})
        except Exception as e:
            print("Failed to broadcast review_updated:", e)
        return Response(d)

from .models import ContactMessage
from .serializers import ContactMessageSerializer

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def contact_messages(request):
    if request.method == "GET":
        qs = ContactMessage.objects.all().select_related('user', 'product').order_by('-created_at')
        serializer = ContactMessageSerializer(qs, many=True)
        return Response(serializer.data)
        
    # POST
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user if request.user.is_authenticated else None
        msg = serializer.save(user=user)
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("message_created", {"message": ContactMessageSerializer(msg).data})
        except Exception as e:
            print("Failed to broadcast message_created:", e)
        return Response(ContactMessageSerializer(msg).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["PUT", "DELETE"])
@permission_classes([AllowAny])
def contact_message_detail(request, message_id: int):
    try:
        msg = ContactMessage.objects.get(id=message_id)
    except ContactMessage.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == "DELETE":
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("message_deleted", {"message_id": message_id})
        except Exception as e:
            print("Failed to broadcast message_deleted:", e)
        msg.delete()
        return Response({"deleted": True})
        
    # PUT to mark as read or reply
    updated = False
    if "is_read" in request.data:
        msg.is_read = request.data["is_read"]
        updated = True
        
    if "reply" in request.data:
        msg.reply = request.data["reply"]
        msg.is_read = True
        updated = True
        # Create notification for user
        if msg.user:
            from identity.models import Notification
            Notification.objects.create(
                user=msg.user,
                title=f"Jogap geldi: {msg.subject[:30]}...",
                message=msg.reply,
                type="reply"
            )
            
    if updated:
        msg.save()
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("message_updated", {"message": ContactMessageSerializer(msg).data})
        except Exception as e:
            print("Failed to broadcast message_updated:", e)

    return Response(ContactMessageSerializer(msg).data)

from rest_framework import viewsets
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Order.objects.none()
        if user.is_staff or user.is_superuser:
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            order = serializer.save(user=self.request.user)
        else:
            order = serializer.save()
        
        # Broadcast via WebSocket
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("commerce_order_created", {"order": OrderSerializer(order).data})
        except Exception as e:
            print("Failed to broadcast commerce_order_created:", e)

    def perform_update(self, serializer):
        order = serializer.save()
        # Broadcast via WebSocket
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("commerce_order_updated", {"order": OrderSerializer(order).data})
        except Exception as e:
            print("Failed to broadcast commerce_order_updated:", e)

    def perform_destroy(self, instance):
        order_id = instance.id
        instance.delete()
        # Broadcast via WebSocket
        try:
            from management.ws_utils import broadcast_order_event
            broadcast_order_event("commerce_order_deleted", {"order_id": order_id})
        except Exception as e:
            print("Failed to broadcast commerce_order_deleted:", e)
