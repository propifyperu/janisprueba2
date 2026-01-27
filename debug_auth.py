#!/usr/bin/env python
"""Script para debuggear problemas de autenticación"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from django.contrib.sessions.models import Session
from users.models import CustomUser

print("=" * 50)
print("DEBUG DE AUTENTICACIÓN")
print("=" * 50)

# 1. Limpiar todas las sesiones
print("\n1. Limpiando sesiones...")
session_count = Session.objects.all().count()
Session.objects.all().delete()
print(f"   ✓ {session_count} sesiones eliminadas")

# 2. Verificar usuarios activos
print("\n2. Verificando usuarios...")
all_users = CustomUser.objects.all()
print(f"   Total usuarios: {all_users.count()}")

for user in all_users:
    status = "✓ ACTIVO" if user.is_active else "✗ INACTIVO"
    print(f"   - {user.username}: {status}")
    if not user.is_active:
        print(f"     ⚠ Usuario '{user.username}' está INACTIVO")

# 3. Verificar superusuarios
superusers = CustomUser.objects.filter(is_superuser=True, is_active=True)
print(f"\n3. Superusuarios activos: {superusers.count()}")
for su in superusers:
    print(f"   - {su.username} (email: {su.email})")

print("\n" + "=" * 50)
print("RESUMEN:")
print("- Todas las sesiones han sido limpiadas")
print("- Abre una ventana de incógnito en tu navegador")
print("- Ve a http://127.0.0.1:8000/users/login/")
print("- Usa un usuario ACTIVO para hacer login")
print("=" * 50)
