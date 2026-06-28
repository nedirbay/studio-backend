import os
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')
    django.setup()

    from management.models import OrderType, Service

    print("--- Seeding Studio Order Meta ---")

    # Add Order Types
    order_types = ["Gyz toý", "Gelin toý", "Doglan gün", "Sünnet toý", "Sazly agşam"]
    for ot_name in order_types:
        ot, created = OrderType.objects.get_or_create(name=ot_name)
        if created:
            print(f"Created OrderType: {ot_name}")
        else:
            print(f"OrderType already exists: {ot_name}")

    # Add Services
    services = ["Suratçy", "Kameraçy", "Montažçy", "Yşykçy", "Dron operatorlar"]
    for s_name in services:
        s, created = Service.objects.get_or_create(name=s_name)
        if created:
            print(f"Created Service: {s_name}")
        else:
            print(f"Service already exists: {s_name}")

    print("--- Seeding Completed successfully ---")

if __name__ == '__main__':
    main()
