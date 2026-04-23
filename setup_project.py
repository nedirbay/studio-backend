import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from identity.models import Role
import populate_db
import seed_blogs

User = get_user_model()

def setup_project():
    print("--- Project Setup Started ---")

    # 1. Create Roles
    print("\n[1/4] Creating Roles...")
    admin_role, _ = Role.objects.get_or_create(name='Admin', defaults={'description': 'System Administrator'})
    customer_role, _ = Role.objects.get_or_create(name='Customer', defaults={'description': 'Regular Customer'})
    print(f"Roles initialized: {admin_role.name}, {customer_role.name}")

    # 2. Create Admin User
    print("\n[2/4] Creating Admin User...")
    admin_username = 'admin'
    admin_email = 'admin@studio.com'
    admin_password = 'adminpassword123'

    if not User.objects.filter(username=admin_username).exists():
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        admin_user.role = admin_role
        admin_user.save()
        print(f"Admin user created!")
        print(f"Username: {admin_username}")
        print(f"Password: {admin_password}")
    else:
        print(f"Admin user '{admin_username}' already exists.")

    # 3. Populate Commerce Data
    print("\n[3/4] Seeding Commerce Data (Categories, Products, Brands)...")
    try:
        populate_db.populate()
        print("Commerce data seeded successfully.")
    except Exception as e:
        print(f"Error seeding commerce data: {e}")

    # 4. Populate Blog Data
    print("\n[4/4] Seeding Blog Data...")
    try:
        seed_blogs.populate_blogs()
        print("Blog data seeded successfully.")
    except Exception as e:
        print(f"Error seeding blog data: {e}")

    print("\n--- Project Setup Completed Successfully! ---")
    print("You can now login with the admin credentials provided above.")

if __name__ == '__main__':
    setup_project()
