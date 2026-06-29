import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from identity.models import Role

User = get_user_model()

def create_or_update_account(username, email, password, role_name, is_staff_and_superuser=False):
    # Fetch or create the custom role
    role, _ = Role.objects.get_or_create(name=role_name)
    
    # Fetch existing user or create a default instance
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_staff': is_staff_and_superuser,
        'is_superuser': is_staff_and_superuser,
    })
    
    # Apply security privileges and authentication details
    user.email = email
    user.set_password(password)
    user.role = role
    user.is_staff = is_staff_and_superuser
    user.is_superuser = is_staff_and_superuser
    user.save()
    
    action = "created" if created else "updated"
    print(f"User Account: '{username}' successfully {action}!")
    print(f"  - Email: {email}")
    print(f"  - Role: {role_name}")
    print(f"  - Password: {password}")
    print(f"  - Superuser Status: {is_staff_and_superuser}")
    print("-" * 50)

def main():
    print("=" * 60)
    print("SEEDING TEST ACCOUNTS (1 ADMIN, 1 REGULAR USER)")
    print("=" * 60)
    
    # 1) Admin Account
    create_or_update_account(
        username="test_admin",
        email="test_admin@studio.com",
        password="test_admin_pass123",
        role_name="Admin",
        is_staff_and_superuser=True
    )
    
    # 2) Regular Customer Account
    create_or_update_account(
        username="test_user",
        email="test_user@studio.com",
        password="test_user_pass123",
        role_name="Customer",
        is_staff_and_superuser=False
    )
    
    print("Test accounts seeding completed successfully.")
    print("=" * 60)

if __name__ == "__main__":
    main()
