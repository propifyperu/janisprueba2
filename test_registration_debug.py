#!/usr/bin/env python
"""
Script para debuggear el flujo de registro
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from django.test import Client
from users.models import CustomUser
from security.models import AuthorizedDevice

def test_registration():
    """Test del flujo de registro"""
    
    # Limpiar usuarios de prueba anteriores
    CustomUser.objects.filter(username='testuser_debug').delete()
    
    client = Client()
    
    print("="*60)
    print("TEST DE REGISTRO")
    print("="*60)
    
    # Test 1: Obtener formulario de registro
    print("\n1. Obteniendo formulario de registro...")
    response = client.get('/users/register/')
    if response.status_code == 200:
        print("   ✓ Página de registro accesible (200)")
    else:
        print(f"   ✗ Error: {response.status_code}")
        return False
    
    # Test 2: Enviar formulario POST
    print("\n2. Enviando formulario de registro...")
    data = {
        'username': 'testuser_debug',
        'email': 'testdebug@example.com',
        'first_name': 'Test',
        'last_name': 'Debug',
        'password': 'TestPass123!@',
        'password_confirm': 'TestPass123!@',
        'phone': '999888777'
    }
    
    response = client.post('/users/register/', data, follow=False)
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"   ✓ Redirect a: {response.url}")
    elif response.status_code == 200:
        # Mostrar errores del formulario
        print("   ✗ Formulario no fue aceptado. Errores:")
        if hasattr(response, 'context') and 'form' in response.context:
            form = response.context['form']
            for field, errors in form.errors.items():
                print(f"      {field}: {errors}")
        return False
    
    # Test 3: Verificar que el usuario fue creado
    print("\n3. Verificando que el usuario fue creado en DB...")
    try:
        user = CustomUser.objects.get(username='testuser_debug')
        print(f"   ✓ Usuario creado: {user.username}")
        print(f"   ✓ Email: {user.email}")
        print(f"   ✓ Nombre: {user.first_name} {user.last_name}")
        print(f"   ✓ is_active: {user.is_active} (debe ser False)")
    except CustomUser.DoesNotExist:
        print("   ✗ ERROR: Usuario NO fue creado en la base de datos")
        return False
    
    # Test 4: Verificar que el dispositivo fue creado
    print("\n4. Verificando que el dispositivo fue creado...")
    devices = AuthorizedDevice.objects.filter(user=user)
    if devices.exists():
        device = devices.first()
        print(f"   ✓ Dispositivo creado")
        print(f"   ✓ ID del dispositivo: {device.id}")
        print(f"   ✓ Status: {device.status}")
        print(f"   ✓ Platform: {device.platform}")
    else:
        print("   ✗ ERROR: Dispositivo NO fue creado")
        return False
    
    # Test 5: Verificar acceso a página de verificación
    print("\n5. Accediendo a página de verificación de dispositivo...")
    response = client.get(f'/security/verify-device/{device.id}/')
    if response.status_code == 200:
        print(f"   ✓ Página de verificación accesible (200)")
        content = response.content.decode('utf-8')
        if 'Verifica tu Dispositivo' in content:
            print("   ✓ Contenido correcto")
        else:
            print("   ✗ Contenido no esperado")
    else:
        print(f"   ✗ Error: {response.status_code}")
        return False
    
    print("\n" + "="*60)
    print("✓ TODOS LOS TESTS PASARON")
    print("="*60)
    
    # Limpiar
    device.delete()
    user.delete()
    
    return True

if __name__ == '__main__':
    try:
        test_registration()
    except Exception as e:
        print(f"\n✗ ERROR EXCEPCIONAL: {str(e)}")
        import traceback
        traceback.print_exc()
