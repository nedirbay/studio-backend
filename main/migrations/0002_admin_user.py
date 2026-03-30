from django.db import migrations


ADMIN_TOKEN = "admin_token_12345"


def seed_admin(apps, schema_editor):
    Role = apps.get_model("main", "Role")
    User = apps.get_model("main", "User")

    role, _ = Role.objects.get_or_create(name="admin")
    User.objects.get_or_create(
        token=ADMIN_TOKEN,
        defaults={
            "name": "Admin",
            "role": role,
            "is_active": True,
            "salary": 0,
            "phone": "",
            "avatar_path": "",
        },
    )


def unseed_admin(apps, schema_editor):
    User = apps.get_model("main", "User")
    User.objects.filter(token=ADMIN_TOKEN).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_admin, reverse_code=unseed_admin),
    ]
