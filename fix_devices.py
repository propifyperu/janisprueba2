import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
import django
django.setup()

from security.models import AuthorizedDevice

updated = AuthorizedDevice.objects.filter(status='approve').update(status='approved')
print(f'Actualizados {updated} dispositivos de "approve" a "approved"')

# Verificar
devices = AuthorizedDevice.objects.filter(status='approved')
print(f'Total dispositivos aprobados: {devices.count()}')
