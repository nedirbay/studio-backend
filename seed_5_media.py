import os
import urllib.request
from pathlib import Path
import django

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studio_api.settings")
    django.setup()

from django.conf import settings
from photostudio.models import PhotoStudioImage, PhotoStudioVideo
from photostudio.services import generate_hls_for_video

# Media items data using reliable URLs
VIDEOS_DATA = [
    {
        "title": "Tebigat we Towşanlar (Big Buck Bunny)",
        "description": "Towşanyň başyndan geçiren gyzykly wakalaryndan gysgaça wideo.",
        "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "thumb_url": "https://images.pexels.com/photos/3225517/pexels-photo-3225517.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Aýy we tebigat (Bear Video)",
        "description": "Studiýada taýýarlanylan wild-life aýy şekili.",
        "video_url": "https://www.w3schools.com/html/movie.mp4",
        "thumb_url": "https://images.pexels.com/photos/1001682/pexels-photo-1001682.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Doganlar toý pursatlary",
        "description": "Toý gününden gysgaça wideo we iň täsirli pursatlar.",
        "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "thumb_url": "https://images.pexels.com/photos/2215609/pexels-photo-2215609.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Neon yşykly portret",
        "description": "Gije gurlan neon yşyklarynyň astyndaky portret wideo.",
        "video_url": "https://www.w3schools.com/html/movie.mp4",
        "thumb_url": "https://images.pexels.com/photos/210186/pexels-photo-210186.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "FotoStudio tanyşdyryş",
        "description": "Doganlar foto merkezinden studiýa tanyşdyryş wideosy.",
        "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "thumb_url": "https://images.pexels.com/photos/356079/pexels-photo-356079.jpeg?auto=compress&cs=tinysrgb&w=400"
    }
]

IMAGES_DATA = [
    {
        "title": "Kamera we enjamlar",
        "description": "Professional suratçylyk üçin zerur bolan esasy enjamlar we aksessuarlar.",
        "image_url": "https://images.pexels.com/photos/3379942/pexels-photo-3379942.jpeg?auto=compress&cs=tinysrgb&w=800",
        "thumb_url": "https://images.pexels.com/photos/3379942/pexels-photo-3379942.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Döredijilikli iş ýeri",
        "description": "Foto we wideo redaktirlemek üçin guralan häzirki zaman iş stoly.",
        "image_url": "https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&w=800",
        "thumb_url": "https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Studio monitorlar gurluşy",
        "description": "Ajaýyp reňk takyklygy üçin studiýada ulanylýan professional monitorlar.",
        "image_url": "https://images.pexels.com/photos/1714208/pexels-photo-1714208.jpeg?auto=compress&cs=tinysrgb&w=800",
        "thumb_url": "https://images.pexels.com/photos/1714208/pexels-photo-1714208.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Kamera obýektiwi",
        "description": "Çuňlugy we durylygy üpjün edýän ýokary hilli kamera obýektiwi.",
        "image_url": "https://images.pexels.com/photos/225157/pexels-photo-225157.jpeg?auto=compress&cs=tinysrgb&w=800",
        "thumb_url": "https://images.pexels.com/photos/225157/pexels-photo-225157.jpeg?auto=compress&cs=tinysrgb&w=400"
    },
    {
        "title": "Professional fotoapparat",
        "description": "Studiýa şertlerinde portretleri we peýzajlary düşürmek üçin kamera.",
        "image_url": "https://images.pexels.com/photos/257736/pexels-photo-257736.jpeg?auto=compress&cs=tinysrgb&w=800",
        "thumb_url": "https://images.pexels.com/photos/257736/pexels-photo-257736.jpeg?auto=compress&cs=tinysrgb&w=400"
    }
]

def download_file(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        print(f"Downloading: {url} -> {dest_path}")
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"Downloaded successfully: {dest_path.name}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}. Creating dummy file.")
        with open(dest_path, "wb") as dummy:
            dummy.write(b"dummy")
        return False

def main():
    media_root = Path(settings.MEDIA_ROOT)
    
    # 1. Clean existing records
    print("Deleting old PhotoStudioVideo and PhotoStudioImage records...")
    PhotoStudioVideo.objects.all().delete()
    PhotoStudioImage.objects.all().delete()

    # 2. Seed Videos
    print("\n--- Seeding 5 Videos ---")
    for i, item in enumerate(VIDEOS_DATA, 1):
        video_filename = f"video_{i}.mp4"
        thumb_filename = f"video_{i}_thumb.jpg"
        
        video_path = media_root / "photostudio" / "videos" / video_filename
        thumb_path = media_root / "photostudio" / "videos" / "thumbnails" / thumb_filename
        
        download_file(item["video_url"], video_path)
        download_file(item["thumb_url"], thumb_path)
        
        video_db_path = f"photostudio/videos/{video_filename}"
        thumb_db_path = f"photostudio/videos/thumbnails/{thumb_filename}"
        
        video_obj = PhotoStudioVideo.objects.create(
            title=item["title"],
            description=item["description"],
            video=video_db_path,
            thumbnail_image=thumb_db_path,
            hls_status="pending"
        )
        print(f"Created PhotoStudioVideo ID={video_obj.id}: {video_obj.title}")
        
        # Try HLS generation if ffmpeg is available
        print(f"Running HLS generation for Video ID={video_obj.id}...")
        generate_hls_for_video(video_obj)
        # Reload object to see updated status
        video_obj.refresh_from_db()
        print(f"Video ID={video_obj.id} HLS status: {video_obj.hls_status}")

    # 3. Seed Images
    print("\n--- Seeding 5 Images ---")
    for i, item in enumerate(IMAGES_DATA, 1):
        image_filename = f"image_{i}.jpg"
        thumb_filename = f"image_{i}_thumb.jpg"
        
        image_path = media_root / "photostudio" / "images" / image_filename
        thumb_path = media_root / "photostudio" / "images" / "thumbnails" / thumb_filename
        
        download_file(item["image_url"], image_path)
        download_file(item["thumb_url"], thumb_path)
        
        image_db_path = f"photostudio/images/{image_filename}"
        thumb_db_path = f"photostudio/images/thumbnails/{thumb_filename}"
        
        image_obj = PhotoStudioImage.objects.create(
            title=item["title"],
            description=item["description"],
            image=image_db_path,
            thumbnail_image=thumb_db_path
        )
        print(f"Created PhotoStudioImage ID={image_obj.id}: {image_obj.title}")

    print("\nSeeding finished successfully!")

if __name__ == "__main__":
    main()
