import os
from datetime import timedelta
from decimal import Decimal

import django

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studio_api.settings")
    django.setup()

from django.utils import timezone
from django.db import connection

from gifts.models import Campaign, CampaignParticipation, CampaignRule, CampaignWinner
from identity.models import Role, User
from main.models import Banner, Promo
from photostudio.models import (
    PhotoCategory,
    PhotoCollection,
    PhotoReel,
    PhotoReelComment,
    PhotoReelLike,
    PhotoReelShare,
    PhotoReelTag,
)


def get_or_create_user(username: str, email: str, role: Role) -> User:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "is_active": True,
            "is_email_verified": True,
        },
    )
    if created:
        user.set_password("seedpassword123")
        user.save(update_fields=["password"])
    return user


def sync_pk_sequence(model) -> None:
    table = model._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table}",
            [table],
        )


def seed_photostudio() -> None:
    studio_role, _ = Role.objects.get_or_create(name="Studio")
    author = get_or_create_user("studio", "studio@example.com", studio_role)
    commenter = get_or_create_user("customer1", "customer1@example.com", studio_role)

    wedding, _ = PhotoCategory.objects.get_or_create(name="Toý", defaults={"slug": "toy"})
    portrait, _ = PhotoCategory.objects.get_or_create(name="Portret", defaults={"slug": "portret"})
    wedding_videos, _ = PhotoCollection.objects.update_or_create(
        title="Toý wideolary",
        kind="video",
        defaults={
            "category": wedding,
            "description": "Toý gününden saýlanan dinamiki wideolar we iň gowy pursatlar.",
            "cover_url": "https://images.pexels.com/photos/31370702/pexels-photo-31370702.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "sort_order": 1,
            "is_published": True,
        },
    )
    portrait_videos, _ = PhotoCollection.objects.update_or_create(
        title="Portret wideolary",
        kind="video",
        defaults={
            "category": portrait,
            "description": "Studiýada düşürilen portret wideolary.",
            "cover_url": "https://images.pexels.com/photos/842811/pexels-photo-842811.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "sort_order": 2,
            "is_published": True,
        },
    )
    portrait_photos, _ = PhotoCollection.objects.update_or_create(
        title="Portret suratlary",
        kind="image",
        defaults={
            "category": portrait,
            "description": "Ýumşak yşykly studiýa portret ýygyndysy.",
            "cover_url": "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "sort_order": 3,
            "is_published": True,
        },
    )
    wedding_photos, _ = PhotoCollection.objects.update_or_create(
        title="Toý suratlary",
        kind="image",
        defaults={
            "category": wedding,
            "description": "Toý albomyndan saýlanan iň gowy suratlar.",
            "cover_url": "https://images.pexels.com/photos/1024960/pexels-photo-1024960.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "sort_order": 4,
            "is_published": True,
        },
    )

    reel_1, _ = PhotoReel.objects.update_or_create(
        media_url="https://images.pexels.com/photos/31370702/pexels-photo-31370702.jpeg?auto=compress&cs=tinysrgb&w=1200",
        defaults={
            "category": wedding,
            "collection": wedding_videos,
            "author": author,
            "title": "Doganlar toý pursatlary",
            "description": "Toý gününden gysgaça wideo we iň täsirli pursatlar.",
            "kind": "video",
            "thumbnail_url": "https://images.pexels.com/photos/31370702/pexels-photo-31370702.jpeg?auto=compress&cs=tinysrgb&w=800",
            "duration": 23,
            "music_title": "Wedding Highlights",
            "is_published": True,
        },
    )
    reel_2, _ = PhotoReel.objects.update_or_create(
        media_url="https://videos.pexels.com/video-files/3015488/3015488-hd_1080_1920_24fps.mp4",
        defaults={
            "category": wedding,
            "collection": wedding_videos,
            "author": author,
            "title": "Sahnadaky çykyş",
            "description": "Toýdan joşgunly sahna pursatlary.",
            "kind": "video",
            "thumbnail_url": "https://images.pexels.com/photos/3014856/pexels-photo-3014856.jpeg?auto=compress&cs=tinysrgb&w=800",
            "duration": 19,
            "music_title": "Live Celebration",
            "is_published": True,
        },
    )
    reel_3, _ = PhotoReel.objects.update_or_create(
        media_url="https://videos.pexels.com/video-files/6954203/6954203-hd_1080_1920_25fps.mp4",
        defaults={
            "category": portrait,
            "collection": portrait_videos,
            "author": author,
            "title": "Portret backstage",
            "description": "Portret sessiýasynyň kamera arkasy.",
            "kind": "video",
            "thumbnail_url": "https://images.pexels.com/photos/842811/pexels-photo-842811.jpeg?auto=compress&cs=tinysrgb&w=800",
            "duration": 15,
            "music_title": "Studio Mood",
            "is_published": True,
        },
    )
    reel_4, _ = PhotoReel.objects.update_or_create(
        media_url="https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=1200",
        defaults={
            "category": portrait,
            "collection": portrait_photos,
            "author": author,
            "title": "Portret sessiýasy",
            "description": "Ýumşak yşyk bilen studiýa portret toplumy.",
            "kind": "image",
            "thumbnail_url": "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=800",
            "duration": 0,
            "music_title": "",
            "is_published": True,
        },
    )
    reel_5, _ = PhotoReel.objects.update_or_create(
        media_url="https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=1200",
        defaults={
            "category": portrait,
            "collection": portrait_photos,
            "author": author,
            "title": "Ak fonda portret",
            "description": "Minimal studiýa portret kadry.",
            "kind": "image",
            "thumbnail_url": "https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=800",
            "duration": 0,
            "music_title": "",
            "is_published": True,
        },
    )
    reel_6, _ = PhotoReel.objects.update_or_create(
        media_url="https://images.pexels.com/photos/1024960/pexels-photo-1024960.jpeg?auto=compress&cs=tinysrgb&w=1200",
        defaults={
            "category": wedding,
            "collection": wedding_photos,
            "author": author,
            "title": "Toý albomy",
            "description": "Couple session-den romantik kadrlar.",
            "kind": "image",
            "thumbnail_url": "https://images.pexels.com/photos/1024960/pexels-photo-1024960.jpeg?auto=compress&cs=tinysrgb&w=800",
            "duration": 0,
            "music_title": "",
            "is_published": True,
        },
    )

    for reel, tags in (
        (reel_1, ["toy", "wedding", "video"]),
        (reel_2, ["stage", "celebration", "video"]),
        (reel_3, ["portrait", "studio", "video"]),
        (reel_4, ["portrait", "studio"]),
        (reel_5, ["portrait", "white-bg"]),
        (reel_6, ["wedding", "album"]),
    ):
        existing = set(reel.tags.values_list("name", flat=True))
        for tag_name in tags:
            if tag_name not in existing:
                PhotoReelTag.objects.create(reel=reel, name=tag_name)

    PhotoReelLike.objects.get_or_create(reel=reel_1, user=commenter)
    PhotoReelShare.objects.get_or_create(reel=reel_1, user=commenter, channel="instagram")

    root_comment, _ = PhotoReelComment.objects.get_or_create(
        reel=reel_1,
        user=commenter,
        parent=None,
        text="Ajaýyp taýýarlyk bolupdyr!",
    )
    PhotoReelComment.objects.get_or_create(
        reel=reel_1,
        user=author,
        parent=root_comment,
        text="Sag boluň, täzelerini hem goşarys.",
    )


def seed_gifts() -> None:
    studio_role, _ = Role.objects.get_or_create(name="Studio")
    participant_user = get_or_create_user("campaign_user", "campaign@example.com", studio_role)
    now = timezone.now()

    campaign, _ = Campaign.objects.update_or_create(
        title="Kamera sowgat bäsleşigi",
        defaults={
            "type": "giveaway",
            "subtitle": "Her aý bir ýeňiji",
            "description": "Doganlar foto merkezinden professional kamera utmak üçin gatnaşyň.",
            "image_url": "https://images.pexels.com/photos/51383/photo-camera-subject-photographer-51383.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "banner_url": "https://images.pexels.com/photos/51383/photo-camera-subject-photographer-51383.jpeg?auto=compress&cs=tinysrgb&w=1600",
            "bg_gradient": "from-red-600 to-orange-500",
            "prize_title": "Sony Alpha kamera",
            "prize_value": Decimal("12500.00"),
            "prize_image": "https://images.pexels.com/photos/90946/pexels-photo-90946.jpeg?auto=compress&cs=tinysrgb&w=800",
            "starts_at": now - timedelta(days=2),
            "ends_at": now + timedelta(days=10),
            "rules": "1. Instagramda bizi belläň\n2. Dostlaryňyzy taglaň",
            "winners_count": 1,
            "is_featured": True,
            "status": "active",
        },
    )

    for order, text in enumerate(
        [
            "Instagram sahypamyzy yzarlaň",
            "Soňky postuň aşagyna 2 dostuňyzy belläň",
            "Arza görnüşini dolduryň",
        ],
        start=1,
    ):
        CampaignRule.objects.update_or_create(
            campaign=campaign,
            order=order,
            defaults={"text": text},
        )

    approved_participation, _ = CampaignParticipation.objects.get_or_create(
        campaign=campaign,
        user=participant_user,
        defaults={
            "full_name": "Merdan Ataýew",
            "phone": "+99361000000",
            "email": participant_user.email,
            "status": "approved",
        },
    )
    CampaignParticipation.objects.get_or_create(
        campaign=campaign,
        user=None,
        full_name="Aýna Geldiýewa",
        phone="+99362000000",
        email="ayna@example.com",
        defaults={"status": "pending"},
    )
    CampaignWinner.objects.get_or_create(
        campaign=campaign,
        participant=approved_participation,
        defaults={"prize_title": "Sony Alpha kamera"},
    )


def seed_main_content() -> None:
    sync_pk_sequence(Banner)
    sync_pk_sequence(Promo)

    Banner.objects.update_or_create(
        title="Professional kameralar",
        defaults={
            "subtitle": "Täze gelen model",
            "description": "Sony, Canon we Nikon kameralary bilen studiýaňyzy güýçlendiriň.",
            "image_url": "https://images.pexels.com/photos/90946/pexels-photo-90946.jpeg?auto=compress&cs=tinysrgb&w=1400",
            "cta_text": "Kameralary gör",
            "bg_color": "from-red-900/80",
        },
    )
    Banner.objects.update_or_create(
        title="Aksessuar toplumlary",
        defaults={
            "subtitle": "Tripod, yşyk, mikrofon",
            "description": "Foto we wideonyňyz üçin zerur ähli aksessuarlar bir ýerde.",
            "image_url": "https://images.pexels.com/photos/3379942/pexels-photo-3379942.jpeg?auto=compress&cs=tinysrgb&w=1400",
            "cta_text": "Aksessuarlary aç",
            "bg_color": "from-orange-900/80",
        },
    )

    Promo.objects.update_or_create(
        title="Canon we Sony kameralar",
        defaults={
            "subtitle": "15% çenli arzanladyş",
            "badge": "Top isleg",
            "image_url": "https://images.pexels.com/photos/225157/pexels-photo-225157.jpeg?auto=compress&cs=tinysrgb&w=900",
            "link_url": "/home",
            "bg_gradient": "from-red-800/85",
        },
    )
    Promo.objects.update_or_create(
        title="Studiýa yşyk enjamlary",
        defaults={
            "subtitle": "Täze kolleksiýa",
            "badge": "Täze",
            "image_url": "https://images.pexels.com/photos/2693212/pexels-photo-2693212.jpeg?auto=compress&cs=tinysrgb&w=900",
            "link_url": "/studio",
            "bg_gradient": "from-slate-900/85",
        },
    )


def main() -> None:
    seed_photostudio()
    seed_gifts()
    seed_main_content()
    print("Studio seed completed.")


if __name__ == "__main__":
    main()
