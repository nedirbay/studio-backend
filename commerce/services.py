from typing import Optional
from django.db import transaction

from commerce.models import Category, Product, ProductMedia


class CategoryService:
    def get_all(self):
        return list(Category.objects.all().order_by('name'))

    def create(self, name: str) -> int:
        cat = Category.objects.create(name=name)
        return cat.id


class ProductService:
    def get_all(self):
        return list(Product.objects.all().order_by('-created_at').select_related('category').prefetch_related('media'))

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return Product.objects.filter(id=product_id).select_related('category').prefetch_related('media').first()

    @transaction.atomic
    def create(self, product_data: dict, media_data: list) -> int:
        product = Product.objects.create(**product_data)
        self._sync_media(product, media_data)
        return product.id

    @transaction.atomic
    def update(self, product_id: int, product_data: dict, media_data: list) -> bool:
        if not Product.objects.filter(id=product_id).exists():
            return False
        Product.objects.filter(id=product_id).update(**product_data)
        product = Product.objects.get(id=product_id)
        self._sync_media(product, media_data)
        return True

    def delete(self, product_id: int) -> bool:
        deleted, _ = Product.objects.filter(id=product_id).delete()
        return deleted > 0

    def _sync_media(self, product: Product, media_data: list):
        if media_data is None:
            return
        ProductMedia.objects.filter(product=product).delete()
        objs = []
        for item in media_data:
            kind = item.get('kind')
            url = item.get('url')
            if kind not in {'image', 'video'} or not url:
                continue
            objs.append(ProductMedia(product=product, kind=kind, url=url))
        if objs:
            ProductMedia.objects.bulk_create(objs)
