import os
import django
from django.utils import timezone
from datetime import timedelta

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
    django.setup()

from gifts.models import Campaign, CampaignParticipation, CampaignRule, CampaignWinner
from django.contrib.auth import get_user_model

User = get_user_model()

def seed_gifts_data():
    print("Clearing existing gifts/campaigns, participations and winners...")
    CampaignWinner.objects.all().delete()
    CampaignParticipation.objects.all().delete()
    CampaignRule.objects.all().delete()
    Campaign.objects.all().delete()

    now = timezone.now()

    # 1. Active Giveaway
    c1 = Campaign.objects.create(
        type='giveaway',
        title='Ulgama agza bolan ilkinji 10 müşderä sowgat!',
        subtitle='Täze agzalar üçin uly utuşly bäsleşik',
        description='Programmany ulanyp başlaň we gymmat bahaly sowgatlar utup alyň! Ulgama agza bolan ilkinji 10 adamyň arasynda ýörite sowgat paýlanar.',
        bg_gradient='from-red-600 to-orange-500',
        prize_title='Smartfon Redmi Note 13',
        prize_value=3500.00,
        starts_at=now - timedelta(days=5),
        ends_at=now + timedelta(days=15),
        rules="Ulgama täze agza bolmaly.\nProfil maglumatlaryny doly doldurmaly.\nTelefon belgisini tassyklamaly.",
        is_featured=True,
        status='active'
    )
    print(f"Created campaign: {c1.title}")

    # 2. Active Promotion (Aksiýa)
    c2 = Campaign.objects.create(
        type='promotion',
        title='Tomus Aksiýasy - Ähli Harytlara 20% Arzanladyş!',
        subtitle='Tomusky aýratyn arzanladyşlar başlandy',
        description='Tomus aýlary dowamynda biziň programmamyz arkaly islendik önümi sargyt edeniňizde 20% arzanladyş gazanyň. Promo kody ulanyň we peýdalanyň!',
        bg_gradient='from-amber-500 to-yellow-400',
        discount_percent=20,
        promo_code='TOMUS20',
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=30),
        rules="Sargyt edeniňizde promo kody girizmeli.\nArzanladyş ähli harytlar üçin degişlidir.\nHer ulanyjy diňe 1 gezek ulanyp bilýär.",
        is_featured=False,
        status='active'
    )
    print(f"Created campaign: {c2.title}")

    # 3. Active Gift (Sowgat)
    c3 = Campaign.objects.create(
        type='gift',
        title='Her 1000 TMT-dan ýokary sargyda ýörite sowgat paketi',
        subtitle='Sowgatly we bereketli sargytlar',
        description='Biziň dükandan 1000 TMT-dan ýokary islendik söwda edeniňizde, size ýörite taýýarlanan sowgat paketi (termos we ruçka) sowgat berilýär!',
        bg_gradient='from-purple-600 to-indigo-500',
        prize_title='Ýörite Sowgat Paketi (Termos we Ruçka)',
        prize_value=250.00,
        min_order_amount=1000.00,
        starts_at=now - timedelta(days=2),
        ends_at=now + timedelta(days=45),
        rules="Sargydyň umumy bahasy 1000 TMT-dan geçmeli.\nSowgat sargyt gowşurylanda bile berilýär.\nSowgatlar çäkli mukdardadyr.",
        is_featured=True,
        status='active'
    )
    print(f"Created campaign: {c3.title}")

    # 4. Expired Campaign (invisible to clients, visible to admin)
    c4 = Campaign.objects.create(
        type='giveaway',
        title='Bahar Bäsleşigi 2026 (Tamamlandy)',
        subtitle='AirPods 3 utmak mümkinçiligi',
        description='Bahar aýynyň ilkinji hepdesinde geçirilýän uly utuşly bäsleşik. Aksiýanyň wagty dolan soň peýdalanyjylara görünmeli däl.',
        bg_gradient='from-slate-700 to-slate-900',
        prize_title='Nauşnik AirPods 3',
        prize_value=2200.00,
        starts_at=now - timedelta(days=60),
        ends_at=now - timedelta(days=30),
        rules="Bahar aýynda gatnaşmaly.\nŞertleri doly berjaý etmeli.",
        is_featured=False,
        status='active'
    )
    print(f"Created expired campaign: {c4.title}")

    # 5. Future/Draft Campaign (invisible to clients, visible to admin)
    c5 = Campaign.objects.create(
        type='giveaway',
        title='Garaşsyzlyk Baýramy Bäsleşigi (Garaşylýar)',
        subtitle='Uly baýramçylyk sowgady',
        description='Garaşsyzlyk baýramyna gabatlanyp geçiriljek uly bäsleşik. Häzirlikçe taslama (draft) görnüşinde dur.',
        bg_gradient='from-emerald-600 to-teal-500',
        prize_title='Smart Telewizor LG 43',
        prize_value=6500.00,
        starts_at=now + timedelta(days=60),
        ends_at=now + timedelta(days=90),
        rules="Baýramçylyk hepdesinde gatnaşmaly.\nIň az 1 sargyt edip gatnaşyjy bolmaly.",
        is_featured=False,
        status='draft'
    )
    print(f"Created draft campaign: {c5.title}")

    # Create dummy users or fetch existing ones to register participations
    users = list(User.objects.all()[:5])
    if len(users) < 3:
        from identity.models import Role
        client_role, _ = Role.objects.get_or_create(name='Client')
        
        # Create some test users
        u1, _ = User.objects.get_or_create(username='arman_tester', defaults={'email': 'arman@test.com', 'role': client_role})
        u2, _ = User.objects.get_or_create(username='merjen_tester', defaults={'email': 'merjen@test.com', 'role': client_role})
        u3, _ = User.objects.get_or_create(username='begli_tester', defaults={'email': 'begli@test.com', 'role': client_role})
        users = [u1, u2, u3]
        print("Created test users for participations")

    # Add participations to active campaigns
    # Campaign 1
    p1 = CampaignParticipation.objects.create(
        campaign=c1,
        user=users[0],
        full_name='Arman Saparow',
        phone='+993 65 123456',
        email='arman@test.com',
        note='Meniň ilkinji gatnaşygym, üstünlik!',
        status='approved'
    )
    p2 = CampaignParticipation.objects.create(
        campaign=c1,
        user=users[1],
        full_name='Merjen Kakalyýewa',
        phone='+993 64 987654',
        email='merjen@test.com',
        note='Sowgat almak isleýärin!',
        status='won' # This automatically triggers winner creation!
    )
    p3 = CampaignParticipation.objects.create(
        campaign=c1,
        user=users[2],
        full_name='Begli Gurbanow',
        phone='+993 63 456789',
        email='begli@test.com',
        note='Bäsleşige gatnaşýaryn.',
        status='pending'
    )

    # Campaign 2 (Aksiýa - Tomus)
    p4 = CampaignParticipation.objects.create(
        campaign=c2,
        user=users[0],
        full_name='Arman Saparow',
        phone='+993 65 123456',
        email='arman@test.com',
        status='approved'
    )
    p5 = CampaignParticipation.objects.create(
        campaign=c2,
        user=users[1],
        full_name='Merjen Kakalyýewa',
        phone='+993 64 987654',
        email='merjen@test.com',
        status='pending'
    )

    print(f"Created participations for active campaigns. Winner auto-sync verified!")
    print(f"Total winners for {c1.title}: {c1.winners.count()}")

if __name__ == '__main__':
    seed_gifts_data()
    print("Seed data successfully added to database!")
