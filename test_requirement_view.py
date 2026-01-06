"""Test para requirement_create_view"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from django.test import RequestFactory
from users.models import CustomUser
from properties.views import requirement_create_view

try:
    rf = RequestFactory()
    req = rf.get('/dashboard/propiedades/requerimientos/crear/')
    req.user = CustomUser.objects.filter(is_active=True).first()
    
    print(f"Usuario de prueba: {req.user.username}")
    
    response = requirement_create_view(req)
    print(f"✅ Vista ejecutada correctamente")
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.get('Content-Type', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
