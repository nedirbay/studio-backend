import os
import django
import sys
from django.utils.text import slugify

# Add current directory to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')

# Initialize Django
django.setup()

from commerce.models import Product, Category, Brand

def generate_slugs():
    # Update Products
    products = Product.objects.filter(slug__isnull=True) | Product.objects.filter(slug='')
    print(f"Generating slugs for {products.count()} products...")
    for product in products:
        # Django model's save method has custom logic to generate slug, let's call save()
        product.save()
        print(f"Updated product: {product.name} -> {product.slug}")

    # Update Categories
    categories = Category.objects.filter(slug__isnull=True) | Category.objects.filter(slug='')
    print(f"Generating slugs for {categories.count()} categories...")
    for category in categories:
        category.save()
        print(f"Updated category: {category.name} -> {category.slug}")

    # Update Brands
    brands = Brand.objects.filter(slug__isnull=True) | Brand.objects.filter(slug='')
    print(f"Generating slugs for {brands.count()} brands...")
    for brand in brands:
        brand.save()
        print(f"Updated brand: {brand.name} -> {brand.slug}")

if __name__ == '__main__':
    generate_slugs()
    print("Done!")
