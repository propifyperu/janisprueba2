"""Script para probar la API de eventos"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from django.contrib.auth import get_user_model
from properties.models import Event
from properties.views import api_events_json
from django.test import RequestFactory

User = get_user_model()

# Crear una request falsa
factory = RequestFactory()
request = factory.get('/dashboard/propiedades/api/events/')

# Usar el primer usuario (ajusta según sea necesario)
user = User.objects.filter(is_active=True).first()
print(f"\n=== Probando API como usuario: {user.username} (superuser: {user.is_superuser}) ===\n")

request.user = user

# Llamar a la vista
response = api_events_json(request)

# Ver el resultado
print("Status Code:", response.status_code)
print("Content-Type:", response.get('Content-Type'))
print("\nJSON Response:")
import json
data = json.loads(response.content)
print(json.dumps(data, indent=2, ensure_ascii=False))

print(f"\n=== Total eventos retornados: {len(data)} ===\n")
