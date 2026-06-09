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
from photostudio.models import PhotoStudioImage, PhotoStudioVideo


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
    PhotoStudioVideo.objects.update_or_create(
        title="Doganlar toý pursatlary",
        defaults={
            "description": "Toý gününden gysgaça wideo we iň täsirli pursatlar.",
            "thumbnail_image": "photostudio/videos/thumbnails/wedding-highlights.jpg",
            "video": "photostudio/videos/wedding-highlights.mp4",
            "hls_status": "pending",
        },
    )
    PhotoStudioImage.objects.update_or_create(
        title="Portret sessiýasy",
        defaults={
            "description": "Ýumşak yşyk bilen studiýa portret toplumy.",
            "thumbnail_image": "photostudio/images/thumbnails/portrait-session.jpg",
            "image": "photostudio/images/portrait-session.jpg",
        },
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
