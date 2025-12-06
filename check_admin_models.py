#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from security.models import AuthorizedDevice
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

print("\n=== USUARIOS CON DISPOSITIVOS ===\n")

users_with_devices = CustomUser.objects.filter(authorized_devices__isnull=False).distinct()

for user in users_with_devices:
    print(f"\nUSUARIO: {user.username}")
    print("=" * 70)
    
    devices = AuthorizedDevice.objects.filter(user=user).order_by('-id')
    
    for device in devices:
        status_icon = "✓" if device.status == 'approved' else "✗"
        print(f"  {status_icon} ID {device.id}: status='{device.status}'")
        print(f"      device_id: {device.device_id}")
        print(f"      IP: {device.ip_address}")
        print(f"      registered: {device.registered_at}")
        print()
    
    print(f"  TOTAL: {devices.count()} dispositivo(s)")
