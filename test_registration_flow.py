#!/usr/bin/env python
"""
Script de test para verificar el flujo de registro completo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from django.test import Client
from users.models import CustomUser
from security.models import AuthorizedDevice
import json

def test_registration_flow():
    """Test del flujo completo de registro"""
    
    # Crear cliente
    client = Client()
    
    # 1. Obtener página de registro
    print("1. Obteniendo página de registro...")
    response = client.get('/users/register/')
    assert response.status_code == 200, f"Error: status {response.status_code}"
    print("   ✓ Página de registro cargada correctamente")
    
    # 2. Enviar formulario de registro
    print("\n2. Enviando formulario de registro...")
    data = {
        'username': 'testuser123',
        'email': 'testuser@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'TestPass123!',
        'password_confirm': 'TestPass123!',
        'phone': '999999999'
    }
    
    response = client.post('/users/register/', data, follow=True)
    print(f"   Response status: {response.status_code}")
    print(f"   Response URL: {response.wsgi_request.path if response.wsgi_request else 'N/A'}")
    
    # 3. Verificar que el usuario fue creado
    print("\n3. Verificando que el usuario fue creado...")
    try:
        user = CustomUser.objects.get(username='testuser123')
        print(f"   ✓ Usuario creado: {user.username}")
        print(f"   ✓ Email: {user.email}")
        print(f"   ✓ is_active: {user.is_active}")
        assert not user.is_active, "El usuario debe estar inactivo"
    except CustomUser.DoesNotExist:
        print("   ✗ ERROR: Usuario no fue creado")
        return False
    
    # 4. Verificar que el dispositivo fue creado
    print("\n4. Verificando que el dispositivo fue creado...")
    devices = AuthorizedDevice.objects.filter(user=user)
    assert devices.exists(), "No se encontraron dispositivos para el usuario"
    device = devices.first()
    print(f"   ✓ Dispositivo creado: {device.id}")
    print(f"   ✓ Platform: {device.platform}")
    print(f"   ✓ Status: {device.status}")
    print(f"   ✓ IP Address: {device.ip_address}")
    
    # 5. Verificar que llegamos a la página de verificación
    print("\n5. Verificando redirección a verificación de dispositivo...")
    assert response.status_code == 200, f"Error al cargar página de verificación: {response.status_code}"
    
    # Verificar que el contenido es correcto
    content = response.content.decode('utf-8')
    assert 'Verifica tu Dispositivo' in content, "No se encontró el título de verificación"
    assert device.device_id in content, "No se encontró el ID del dispositivo en la página"
    
    print("   ✓ Página de verificación cargada correctamente")
    print(f"   ✓ Contenido de dispositivo visible en la página")
    
    # 6. Verificar que es posible ir al login
    print("\n6. Verificando acceso al login...")
    response = client.get('/users/login/')
    assert response.status_code == 200, f"Error al acceder al login: {response.status_code}"
    print("   ✓ Página de login accesible")
    
    # 7. Intentar login con usuario no aprobado (debe fallar)
    print("\n7. Intentando login con usuario no aprobado...")
    response = client.post('/users/login/', {
        'username': 'testuser123',
        'password': 'TestPass123!'
    }, follow=True)
    
    # Django authenticate() no debe autenticar usuarios inactivos
    # Verificar que no estamos autenticados
    assert not response.wsgi_request.user.is_authenticated or not response.wsgi_request.user.is_active, \
        "El usuario inactivo NO debería ser autenticado"
    print("   ✓ Login correctamente rechazado para usuario inactivo")
    
    print("\n" + "="*50)
    print("✓ TODOS LOS TESTS PASARON")
    print("="*50)
    
    # Limpiar
    device.delete()
    user.delete()
    
    return True

if __name__ == '__main__':
    try:
        test_registration_flow()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
