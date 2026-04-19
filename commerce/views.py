from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from commerce.models import Category, Product, ProductMedia, Brand, Review
from commerce.serializers import CategorySerializer, ProductSerializer
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


def _media_dict(media: ProductMedia):
    return {"id": media.id, "kind": media.kind, "url": media.url, "created_at": media.created_at.isoformat()}

def _product_dict(prod: Product):
    return {
        "id": prod.id,
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
        "media": [_media_dict(m) for m in prod.media.all()],
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
        "helpful": 0 # Not implemented in DB yet, but for frontend compatibility
    }


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def categories(request):
    if request.method == "GET":
        return Response([_category_dict(c) for c in category_service.get_all()])
    serializer = CategorySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    new_id = category_service.create(serializer.validated_data["name"])
    return Response({"id": new_id}, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def products(request):
    if request.method == "GET":
        return Response([_product_dict(p) for p in product_service.get_all()])
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
        return Response(_product_dict(prod))
    if request.method == "PUT":
        serializer = ProductSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        product_data = {}
        for field in ["name", "price", "instock", "marka"]:
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
def brands(request):
    return Response([_brand_dict(b) for b in Brand.objects.all()])


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
    
    return Response(_review_dict(review), status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([AllowAny])
def all_reviews(request):
    reviews = Review.objects.all().select_related('user', 'product').order_by('-created_at')
    # Add product details for admin view
    result = []
    for r in reviews:
        d = _review_dict(r)
        d['productName'] = r.product.name if r.product else 'Näbelli haryt'
        d['productId'] = r.product_id
        result.append(d)
    return Response(result)

@api_view(["DELETE"])
@permission_classes([AllowAny])
def review_detail(request, review_id: int):
    try:
        review = Review.objects.get(id=review_id)
        review.delete()
        return Response({"deleted": True})
    except Review.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)

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
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["PUT", "DELETE"])
@permission_classes([AllowAny])
def contact_message_detail(request, message_id: int):
    try:
        msg = ContactMessage.objects.get(id=message_id)
    except ContactMessage.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == "DELETE":
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
        
    return Response(ContactMessageSerializer(msg).data)
