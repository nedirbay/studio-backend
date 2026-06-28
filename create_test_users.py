import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from identity.models import Role

User = get_user_model()

def create_or_reset_user(username, email, password, role_name, is_admin=False):
    # Get or create role
    role, _ = Role.objects.get_or_create(name=role_name)
    
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_staff': is_admin,
        'is_superuser': is_admin,
    })
    
    # Set password
    user.set_password(password)
    user.role = role
    user.is_staff = is_admin
    user.is_superuser = is_admin
    user.save()
    
    status = "created" if created else "reset"
    print(f"User '{username}' {status} successfully with role '{role_name}' and password '{password}'")

def main():
    print("--- Creating/Resetting 2 Admin and 2 Regular Users ---")
    
    # Admins
    create_or_reset_user("admin1", "admin1@studio.com", "adminpass123", "Admin", is_admin=True)
    create_or_reset_user("admin2", "admin2@studio.com", "adminpass123", "Admin", is_admin=True)
    
    # Regular Users (Customers)
    create_or_reset_user("user1", "user1@studio.com", "userpass123", "Customer", is_admin=False)
    create_or_reset_user("user2", "user2@studio.com", "userpass123", "Customer", is_admin=False)
    
    print("--- Completed! ---")

if __name__ == "__main__":
    main()
