import os
import django
import decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
django.setup()

from django.db import connection
from commerce.models import Category, Product, Brand

def seed_cameras():
    print("=" * 60)
    print("SEEDING CAMERA PRODUCTS (10 ADVERTISEMENT MODELS)")
    print("=" * 60)

    # Sync sequence values to prevent duplicate key errors due to manually specified IDs in populate_db
    with connection.cursor() as cursor:
        cursor.execute("SELECT setval(pg_get_serial_sequence('commerce_category', 'id'), coalesce(max(id), 1), max(id) IS NOT NULL) FROM commerce_category;")
        cursor.execute("SELECT setval(pg_get_serial_sequence('commerce_product', 'id'), coalesce(max(id), 1), max(id) IS NOT NULL) FROM commerce_product;")
        cursor.execute("SELECT setval(pg_get_serial_sequence('commerce_brand', 'id'), coalesce(max(id), 1), max(id) IS NOT NULL) FROM commerce_brand;")
    print("Database sequences successfully synchronized.")

    # 1. Get or Create Category
    category_name = "Foto we Wideo kameralar"
    category_slug = "cameras-video"
    category_icon = "📷"
    
    category, cat_created = Category.objects.get_or_create(
        slug=category_slug,
        defaults={
            'name': category_name,
            'icon': category_icon,
            'count': 10
        }
    )
    if not cat_created:
        category.name = category_name
        category.icon = category_icon
        category.save()
    print(f"Category: '{category.name}' (Slug: {category.slug}) is ready.")

    # 2. Get or Create Brands
    brands_list = [
        {"name": "Sony", "slug": "sony"},
        {"name": "Canon", "slug": "canon"},
        {"name": "Nikon", "slug": "nikon"},
        {"name": "Fujifilm", "slug": "fujifilm"},
        {"name": "Panasonic", "slug": "panasonic"},
        {"name": "Blackmagic", "slug": "blackmagic"},
        {"name": "GoPro", "slug": "gopro"},
        {"name": "DJI", "slug": "dji"}
    ]
    
    for b in brands_list:
        brand, b_created = Brand.objects.get_or_create(
            slug=b["slug"],
            defaults={"name": b["name"], "logo_url": ""}
        )
        if not b_created:
            brand.name = b["name"]
            brand.save()
        print(f"Brand '{brand.name}' is ready.")
    
    print("-" * 50)

    # Clean existing products in this category to ensure clean seeding of exactly 10 products
    deleted_count, _ = Product.objects.filter(category=category).delete()
    if deleted_count > 0:
        print(f"Cleared {deleted_count} existing camera products to prepare a clean slate.")

    # 3. Camera Products Data
    cameras_data = [
        {
            "name": "Sony Alpha 7 IV Professional Gurnam",
            "price": 2499.00,
            "original_price": 2799.00,
            "brand": "Sony",
            "badge": "popular",
            "rating": 4.9,
            "reviews": 124,
            "description": "Sony Alpha 7 IV professional derejeli gibrid aýnasyz kamera. 33 megapiksellik sensor, ýokary tizlikli awtofokus we 4K 60p wideo ýazgy mümkinçiligi bilen islendik çärede professional netije berýär.",
            "features": [
                "33MP Full-Frame Exmor R CMOS Sensor",
                "BIONZ XR Görnüşli Täze Prosessor",
                "Sekuntda 10 kadr çaltlykda surata düşürmek",
                "4K 60p 10-Bit Wideo ýazgysy",
                "5-osly şekil durnuklaşdyryjy (In-Body Stabilization)"
            ],
            "specifications": {
                "Sensor Görnüşi": "Full-Frame (Doly kadr)",
                "Durulygy": "33 MP",
                "Obýektiw Berkidişi": "Sony E-mount",
                "Wideo Format": "4K UHD 60p, 10-bit 4:2:2",
                "ISO Aralygy": "100 - 51200 (Giňeldilen: 50 - 204800)"
            }
        },
        {
            "name": "Canon EOS R6 Mark II Mirrorless Camera",
            "price": 2299.00,
            "original_price": 2499.00,
            "brand": "Canon",
            "badge": "sale",
            "rating": 4.8,
            "reviews": 85,
            "description": "Canon-yň täze nesil aýnasyz kamerasy. 24.2 MP full-frame CMOS sensory we sekuntda 40 kadra çenli elektron ýapgyç tizligi. Dual Pixel CMOS AF II awtofokus ulgamy adam, haýwan we ulaglary dessine tapýar.",
            "features": [
                "24.2MP Full-Frame CMOS Sensor",
                "Dual Pixel CMOS AF II Awtofokus",
                "Elektron ýapgyç bilen sekuntda 40 kadr",
                "4K 60p dury wideo ýazgy",
                "Göz durnuklaşdyryjy we 8-stopa çenli yşyk öwezini doldurma"
            ],
            "specifications": {
                "Sensor Görnüşi": "Full-Frame",
                "Durulygy": "24.2 MP",
                "Obýektiw Berkidişi": "Canon RF-mount",
                "Wideo Format": "4K UHD 60p, 6K RAW (daşarky)",
                "ISO Aralygy": "100 - 102400"
            }
        },
        {
            "name": "Nikon Z6 II Foto/Wideo Guraly",
            "price": 1999.00,
            "original_price": 2199.00,
            "brand": "Nikon",
            "badge": "hot",
            "rating": 4.7,
            "reviews": 92,
            "description": "Ýokary hilli foto we wideo surata düşürmek üçin amatly multimedia guraly. Iki sany EXPEED 6 şekil prosessory, 24.5 MP durulygy we iki sany ýat kartasy üçin slot (CFexpress/XQD + SD).",
            "features": [
                "24.5MP BSI CMOS Sensor",
                "Iki sany EXPEED 6 şekil prosessory",
                "UHD 4K 30p we 4K 60p (krop bilen)",
                "Iki sany ýat kartasy üçin ýer",
                "Gidrawlik ýagdaýda berkidilen korpus"
            ],
            "specifications": {
                "Sensor Görnüşi": "Full-Frame FX-format",
                "Durulygy": "24.5 MP",
                "Obýektiw Berkidişi": "Nikon Z-mount",
                "Wideo Format": "4K UHD 30p / 60p",
                "ISO Aralygy": "100 - 51200"
            }
        },
        {
            "name": "Fujifilm X-T5 Retro Mirrorless",
            "price": 1699.00,
            "original_price": 1799.00,
            "brand": "Fujifilm",
            "badge": "new",
            "rating": 4.8,
            "reviews": 64,
            "description": "Retro dizaýnly we dolandyryş halkaly professional APS-C kamera. Ajaýyp 40.2 MP X-Trans sensory we Fujifilm film simulýasiýalary bilen suratlaryňyz has janly we özboluşly görner.",
            "features": [
                "40.2MP X-Trans CMOS 5 HR Sensory",
                "6.2K 30p we 4K 60p 10-bit wideo",
                "7-stopa çenli korpus durnuklaşdyryjysy",
                "Klassiki retro dizaýnly metal korpus",
                "19 sany meşhur Film Simulýasiýasy"
            ],
            "specifications": {
                "Sensor Görnüşi": "APS-C X-Trans",
                "Durulygy": "40.2 MP",
                "Obýektiw Berkidişi": "Fujifilm X-mount",
                "Wideo Format": "6.2K 30p, 4K 60p",
                "ISO Aralygy": "125 - 12800"
            }
        },
        {
            "name": "Panasonic Lumix GH6 Professional Video",
            "price": 1899.00,
            "original_price": 2099.00,
            "brand": "Panasonic",
            "badge": "pro",
            "rating": 4.9,
            "reviews": 78,
            "description": "Wideo we kino operatorlary üçin ýöriteleşdirilen Micro Four Thirds kamera. 5.7K ýokary durulykly ýazgy, içerki Apple ProRes formatlary we çäksiz wideo ýazgy üçin işjeň sowadyş ulgamy.",
            "features": [
                "25.2MP Live MOS Sensory",
                "5.7K 60p we 4K 120p professional ýazgy",
                "Içerki Apple ProRes 422 HQ / 422 goldawy",
                "Sowadyjy wentilýatorly çäksiz wideo ýazgy",
                "Dinamiki diapazon giňeldiji (DR Boost)"
            ],
            "specifications": {
                "Sensor Görnüşi": "Micro Four Thirds",
                "Durulygy": "25.2 MP",
                "Obýektiw Berkidişi": "Micro Four Thirds mount",
                "Wideo Format": "5.7K 60p, 4K 120p, Apple ProRes",
                "ISO Aralygy": "100 - 25600"
            }
        },
        {
            "name": "Blackmagic Pocket Cinema Camera 6K Pro",
            "price": 2535.00,
            "original_price": 2699.00,
            "brand": "Blackmagic",
            "badge": "cinema",
            "rating": 4.9,
            "reviews": 110,
            "description": "Elde göterip bolýan professional 6K sanly kino kamerasy. Super 35 sensory, dury HDR we 13-stoply dinamiki diapazon. Içine gurnalan 2, 4 we 6-stoply ND filtrleri bilen professional kinoçylyk üçin taýýar.",
            "features": [
                "Super 35 HDR Sensor (6144 x 3456)",
                "Blackmagic RAW we Apple ProRes 10-bit ýazgy",
                "Gurnalan motorly ND filtrler (2, 4, 6 stop)",
                "Dual Native ISO 400 we 3200",
                "Ýokary yşyklandyryşly 5 dýuým egilýän HDR ekran"
            ],
            "specifications": {
                "Sensor Görnüşi": "Super 35",
                "Durulygy": "6144 x 3456",
                "Obýektiw Berkidişi": "EF mount (Canon)",
                "Wideo Format": "6K 60p RAW, 4K ProRes",
                "ISO Aralygy": "Dual Native ISO 400 / 3200 (Maksimum 25600)"
            }
        },
        {
            "name": "Sony FX3 Cinema Line Full-Frame",
            "price": 3899.00,
            "original_price": 3999.00,
            "brand": "Sony",
            "badge": "popular",
            "rating": 5.0,
            "reviews": 142,
            "description": "Sony Cinema Line maşgalasynyň iň kiçi we amatly agzasy. Full-frame sensory, ýokary garaňkyda surata düşürmek ukyby we professional XLR ses portly tutawaç ulgamy bilen ýeke özbaşdak işleýän operatorlar üçin iň gowy saýlaw.",
            "features": [
                "10.2MP Doly kadrly CMOS Sensor (Wideo optimallaşdyrylan)",
                "UHD 4K 120p ýazgy",
                "S-Cinetone professional reňk profili",
                "Gurnalan sowadyjy wentilýator",
                "Aýrylýan professional XLR ses tutawajy"
            ],
            "specifications": {
                "Sensor Görnüşi": "Full-Frame",
                "Durulygy": "10.2 MP",
                "Obýektiw Berkidişi": "Sony E-mount",
                "Wideo Format": "4K UHD 120p, S-Log3/S-Cinetone",
                "ISO Aralygy": "80 - 102400 (Giňeldilen: 409600)"
            }
        },
        {
            "name": "Canon EOS C70 Cinema RF-Mount",
            "price": 5499.00,
            "original_price": 5899.00,
            "brand": "Canon",
            "badge": "professional",
            "rating": 4.9,
            "reviews": 43,
            "description": "Täze nesil RF obýektiw berkidiji bilen Cinema EOS seriýasy. Super 35 DGO (Dual Gain Output) sensory has giň dinamiki diapazony we pes ses arassalygyny üpjün edýär.",
            "features": [
                "Super 35 Dual Gain Output (DGO) Sensor",
                "DCI 4K 120p we 2K 180p ýazgy",
                "Canon Log 2, Log 3 we HDR goldawy",
                "Gurnalan inçe motorly ND filtrleri",
                "Professional I/O portlary we XLR ses birikmesi"
            ],
            "specifications": {
                "Sensor Görnüşi": "Super 35 DGO",
                "Durulygy": "8.85 MP (Kino sensory)",
                "Obýektiw Berkidişi": "Canon RF-mount",
                "Wideo Format": "4K DCI 120p, XF-AVC / MP4",
                "ISO Aralygy": "160 - 25600"
            }
        },
        {
            "name": "GoPro HERO12 Black Action Camera",
            "price": 399.00,
            "original_price": 449.00,
            "brand": "GoPro",
            "badge": "action",
            "rating": 4.7,
            "reviews": 210,
            "description": "Sport, syýahat we ekstremal çäreleri ýazgy etmek üçin dünýäniň iň meşhur ekşn kamerasy. 5.3K wideo, HyperSmooth 6.0 şekil durnuklaşdyryjysy we suwa durnukly berk gurluşy.",
            "features": [
                "5.3K 60p we 4K 120p ekşn wideo",
                "HyperSmooth 6.0 we Horizon Lock",
                "10 metre çenli suw geçirmeýän gorag korpusy",
                "Gurnalan öň we yz tarapky reňkli ekranlar",
                "Giňeldilen batareýa ömri we Bluetooth ses goldawy"
            ],
            "specifications": {
                "Sensor Görnüşi": "1/1.9 dýuým CMOS",
                "Durulygy": "27 MP",
                "Obýektiw Berkidişi": "Gurnalan inçe giň burçly",
                "Wideo Format": "5.3K 60p, 4K 120p, 2.7K 240p",
                "Suw Goragy": "Goşmaça korpussyz 10 metr çenli"
            }
        },
        {
            "name": "DJI Pocket 3 Gimbal Camera",
            "price": 519.00,
            "original_price": 549.00,
            "brand": "DJI",
            "badge": "vlog",
            "rating": 4.8,
            "reviews": 185,
            "description": "Jübiňize sygjak derejede ykjam, gurnalan 3-osly mehaniki durnuklaşdyryjyly (gimbal) kamera. 1-dýuým CMOS sensory we 2-dýuýmlyk öwrülýän sensor ekrany bilen blogerler üçin amatly gural.",
            "features": [
                "Güýçli 1-Dýuýmlyk CMOS Sensor",
                "4K 120p ýokary tizlikli dury ýazgy",
                "3-osly mehaniki şekil durnuklaşdyryjy gimbal",
                "ActiveTrack 6.0 adamy yzarlaýyş ulgamy",
                "2-dýuýmlyk dik/keseligine öwrülýän ekran"
            ],
            "specifications": {
                "Sensor Görnüşi": "1-inch CMOS",
                "Durulygy": "20 MP",
                "Obýektiw Berkidişi": "Gurnalan 20mm f/2.0",
                "Wideo Format": "4K UHD 120p, D-Log M 10-bit",
                "Agramy": "179 gram"
            }
        }
    ]

    # 4. Insert Products
    for item in cameras_data:
        product = Product.objects.create(
            name=item["name"],
            price=decimal.Decimal(item["price"]),
            original_price=decimal.Decimal(item["original_price"]) if "original_price" in item else None,
            instock=True,
            rating=decimal.Decimal(item["rating"]),
            reviews=item["reviews"],
            badge=item["badge"],
            description=item["description"],
            features=item["features"],
            specifications=item["specifications"],
            marka=item["brand"],
            category=category
        )
        print(f"Product '{product.name}' created (Brand: {product.marka}).")

    # Update Category Count
    category.count = Product.objects.filter(category=category).count()
    category.save()
    print("-" * 50)
    print(f"Successfully seeded {category.count} camera products into the database.")
    print("=" * 60)

if __name__ == '__main__':
    seed_cameras()
