import os
import django
import decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
django.setup()

from commerce.models import Category, Product, ProductMedia, Brand
from main.models import Banner, Promo

def populate():
    print("Clearing existing data...")
    ProductMedia.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Brand.objects.all().delete()
    Banner.objects.all().delete()
    Promo.objects.all().delete()

    categories_data = [
        { 'id': 1, 'name': 'Noutbuklar', 'icon': '💻', 'count': 120, 'slug': 'laptops' },
        { 'id': 2, 'name': 'Desktop PK', 'icon': '🖥️', 'count': 85, 'slug': 'desktops' },
        { 'id': 3, 'name': 'Komponentler', 'icon': '🔧', 'count': 340, 'slug': 'components' },
        { 'id': 4, 'name': 'Oýun enjamlary', 'icon': '🎮', 'count': 95, 'slug': 'gaming' },
        { 'id': 5, 'name': 'Monitorlar', 'icon': '🖥', 'count': 60, 'slug': 'monitors' },
        { 'id': 6, 'name': 'Set enjamlary', 'icon': '📡', 'count': 75, 'slug': 'networking' },
        { 'id': 7, 'name': 'Printerler', 'icon': '🖨️', 'count': 45, 'slug': 'printers' },
        { 'id': 8, 'name': 'Aksessuarlar', 'icon': '🎧', 'count': 200, 'slug': 'accessories' },
    ]

    cat_map = {}
    for c in categories_data:
        cat = Category.objects.create(
            id=c['id'],
            name=c['name'],
            slug=c['slug'],
            icon=c['icon'],
            count=c['count']
        )
        cat_map[c['name']] = cat
        print(f"Created category: {cat.name}")

    products_data = [
        {
            'name': 'ASUS ROG Strix G15 Oýun noutbugy',
            'price': 1299,
            'originalPrice': 1599,
            'category': 'Noutbuklar',
            'badge': 'sale',
            'rating': 4.8,
            'reviews': 245,
            'brand': 'ASUS',
            'inStock': True,
            'description': 'ASUS ROG Strix G15 bilen oýun oýnamagyň lezzetini alyň. Iň soňky Intel Core i7 prosessory we NVIDIA GeForce RTX 4070 grafikasy bilen üpjün edilen bu noutbuk ähli oýun zerurlyklaryňyz üçin ajaýyp öndürijilik berýär.',
            'images': [
                'https://images.pexels.com/photos/1229861/pexels-photo-1229861.jpeg?auto=compress&cs=tinysrgb&w=800',
                'https://images.pexels.com/photos/205421/pexels-photo-205421.jpeg?auto=compress&cs=tinysrgb&w=800',
            ],
            'features': ['Intel Core i7-13700H Prosessory', 'NVIDIA GeForce RTX 4070 8GB'],
            'specifications': {'Prosessor': 'Intel Core i7-13700H', 'Grafika': 'NVIDIA RTX 4070 8GB'}
        },
        {
            'name': 'HP Pavilion Desktop i7 16GB RAM',
            'price': 899,
            'category': 'Desktop PK',
            'badge': 'new',
            'rating': 4.6,
            'reviews': 132,
            'brand': 'HP',
            'inStock': True,
            'description': 'HP Pavilion Desktop öndürijilik we güýmenje üçin döredildi.',
            'images': ['https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&w=800'],
            'features': ['Intel Core i7-12700 Prosessory', '16GB DDR4 RAM'],
            'specifications': {'Prosessor': 'Intel Core i7-12700', 'Ýat': '16GB DDR4-3200'}
        },
        {
            'name': 'Samsung 27" 4K IPS Monitor',
            'price': 459,
            'originalPrice': 529,
            'category': 'Monitorlar',
            'badge': 'sale',
            'rating': 4.7,
            'reviews': 189,
            'brand': 'Samsung',
            'inStock': True,
            'description': 'Samsung 27 dýuýmlyk IPS monitory bilen ajaýyp 4K durylygyndan lezzet alyň.',
            'images': ['https://images.pexels.com/photos/1714208/pexels-photo-1714208.jpeg?auto=compress&cs=tinysrgb&w=800'],
            'features': ['27" 4K UHD Durulygy', 'IPS Paneli'],
            'specifications': {'Durulygy': '3840 x 2160', 'Panel': 'IPS'}
        }
    ]

    for p in products_data:
        product = Product.objects.create(
            name=p['name'],
            price=decimal.Decimal(p['price']),
            original_price=decimal.Decimal(p['originalPrice']) if 'originalPrice' in p else None,
            instock=p['inStock'],
            rating=decimal.Decimal(p['rating']),
            reviews=p['reviews'],
            badge=p['badge'],
            description=p['description'],
            features=p['features'],
            specifications=p['specifications'],
            marka=p['brand'],
            category=cat_map[p['category']]
        )
        for img_url in p['images']:
            ProductMedia.objects.create(
                product=product,
                kind='image',
                url=img_url
            )
        print(f"Created product: {product.name}")

    brands_data = [
        { 'id': 1, 'name': 'ASUS', 'slug': 'asus', 'logo_url': '' },
        { 'id': 2, 'name': 'HP', 'slug': 'hp', 'logo_url': '' },
        { 'id': 3, 'name': 'Samsung', 'slug': 'samsung', 'logo_url': '' },
        { 'id': 4, 'name': 'Dell', 'slug': 'dell', 'logo_url': '' },
        { 'id': 5, 'name': 'Apple', 'slug': 'apple', 'logo_url': '' },
        { 'id': 6, 'name': 'Intel', 'slug': 'intel', 'logo_url': '' },
        { 'id': 7, 'name': 'AMD', 'slug': 'amd', 'logo_url': '' },
        { 'id': 8, 'name': 'NVIDIA', 'slug': 'nvidia', 'logo_url': '' },
    ]

    for b in brands_data:
        Brand.objects.create(
            id=b['id'],
            name=b['name'],
            slug=b['slug'],
            logo_url=b['logo_url']
        )
        print(f"Created brand: {b['name']}")

    banners_data = [
        {
            'id': 1,
            'title': 'Güýçli Gaming Kompýuterleri',
            'subtitle': 'Täze gelenler',
            'description': 'Iň soňky nesil NVIDIA RTX grafikasy we ýokary tizlikli prosessorlar bilen oýun dünýäsine çümüň.',
            'image': 'https://images.pexels.com/photos/3165335/pexels-photo-3165335.jpeg?auto=compress&cs=tinysrgb&w=1200',
            'ctaText': 'Söwda et',
            'bgColor': 'from-blue-900/80'
        },
        {
            'id': 2,
            'title': 'Okuw we Iş üçin Noutbuklar',
            'subtitle': 'Uly arzanladyş',
            'description': 'Ykjam, güýçli we amatly noutbuklar bilen iş netijeliligiňizi ýokarlandyryň.',
            'image': 'https://images.pexels.com/photos/129208/pexels-photo-129208.jpeg?auto=compress&cs=tinysrgb&w=1200',
            'ctaText': 'Saýlap al',
            'bgColor': 'from-red-900/80'
        }
    ]

    for b in banners_data:
        Banner.objects.create(
            id=b['id'],
            title=b['title'],
            subtitle=b['subtitle'],
            description=b['description'],
            image_url=b['image'],
            cta_text=b['ctaText'],
            bg_color=b['bgColor']
        )
        print(f"Created banner: {b['title']}")

    promos_data = [
        {
            'title': 'Oýun noutbuklary',
            'subtitle': '25% çenli arzanladyş',
            'badge': '25% çenli arzanladyş',
            'image': 'https://images.pexels.com/photos/1229861/pexels-photo-1229861.jpeg?auto=compress&cs=tinysrgb&w=600',
            'bgGradient': 'from-blue-900/80',
            'link': '#'
        },
        {
            'title': 'PK Komponentleri',
            'subtitle': 'Täze gelenler',
            'badge': 'Täze gelenler',
            'image': 'https://images.pexels.com/photos/3520697/pexels-photo-3520697.jpeg?auto=compress&cs=tinysrgb&w=600',
            'bgGradient': 'from-gray-900/85',
            'link': '#'
        },
        {
            'title': 'Premium Aksessuarlar',
            'subtitle': 'Iň köp satylanlar',
            'badge': 'Iň köp satylanlar',
            'image': 'https://images.pexels.com/photos/3394665/pexels-photo-3394665.jpeg?auto=compress&cs=tinysrgb&w=600',
            'bgGradient': 'from-red-900/85',
            'link': '#'
        }
    ]

    for p in promos_data:
        Promo.objects.create(
            title=p['title'],
            subtitle=p['subtitle'],
            badge=p['badge'],
            image_url=p['image'],
            bg_gradient=p['bgGradient'],
            link_url=p['link']
        )
        print(f"Created promo: {p['title']}")

if __name__ == '__main__':
    populate()
