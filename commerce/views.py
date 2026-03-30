from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from commerce.models import Category, Product, ProductMedia
from commerce.serializers import CategorySerializer, ProductSerializer
from commerce.services import CategoryService, ProductService

category_service = CategoryService()
product_service = ProductService()


def _category_dict(cat: Category):
    return {"id": cat.id, "name": cat.name, "created_at": cat.created_at.isoformat()}


def _media_dict(media: ProductMedia):
    return {"id": media.id, "kind": media.kind, "url": media.url, "created_at": media.created_at.isoformat()}


def _product_dict(prod: Product):
    return {
        "id": prod.id,
        "name": prod.name,
        "price": float(prod.price),
        "instock": prod.instock,
        "created_at": prod.created_at.isoformat(),
        "marka": prod.marka,
        "category_id": prod.category_id,
        "category_name": prod.category.name if prod.category else None,
        "media": [_media_dict(m) for m in prod.media.all()],
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
