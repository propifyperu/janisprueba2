#!/usr/bin/env python
"""
Script para enviar un mensaje de prueba por WhatsApp
"""
import os
import sys
import django
import requests
import json
from dotenv import load_dotenv

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

load_dotenv()

# Obtener credenciales
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v18.0')

# Número de destinatario de prueba
RECIPIENT_PHONE = "+51921055407"  # Número que proporcionaste

print("=" * 70)
print("ENVIAR MENSAJE DE PRUEBA - WHATSAPP BUSINESS API")
print("=" * 70)

# Verificar credenciales
print("\n1. Verificando credenciales...")
if not WHATSAPP_ACCESS_TOKEN:
    print("❌ WHATSAPP_ACCESS_TOKEN no configurado en .env")
    sys.exit(1)
else:
    token_preview = WHATSAPP_ACCESS_TOKEN[:20] + "..." + WHATSAPP_ACCESS_TOKEN[-10:]
    print(f"✅ Token cargado: {token_preview}")

if not WHATSAPP_PHONE_NUMBER_ID:
    print("❌ WHATSAPP_PHONE_NUMBER_ID no configurado en .env")
    print("   Necesitas obtenerlo de Meta Developers → WhatsApp Business → Phone Numbers")
    sys.exit(1)
else:
    print(f"✅ Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")

print(f"📱 Destinatario: {RECIPIENT_PHONE}")

# Enviar mensaje
print("\n2. Enviando mensaje de prueba...")
try:
    url = f"https://graph.instagram.com/{API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": RECIPIENT_PHONE.replace("+", "").replace(" ", ""),
        "type": "text",
        "text": {
            "preview_url": False,
            "body": "¡Hola! Este es un mensaje de prueba desde JanisPropify CRM. Si recibes esto, significa que la integración con WhatsApp está funcionando correctamente. 🎉"
        }
    }
    
    print(f"\n   URL: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"\n   Status Code: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print("✅ ¡Mensaje enviado correctamente!")
        data = response.json()
        message_id = data.get('messages', [{}])[0].get('id')
        print(f"   Message ID: {message_id}")
    else:
        print(f"❌ Error al enviar mensaje: {response.status_code}")
        print(f"   Response: {response.text}")
        
        # Analizar errores comunes
        try:
            error_data = response.json()
            if 'error' in error_data:
                error = error_data['error']
                print(f"\n   Error Details:")
                print(f"   - Code: {error.get('code')}")
                print(f"   - Type: {error.get('type')}")
                print(f"   - Message: {error.get('message')}")
                
                # Sugerencias basadas en el error
                if error.get('code') == 400:
                    print("\n   💡 Sugerencias:")
                    print("   - Verifica que el número de teléfono sea válido (incluyendo código de país)")
                    print("   - El número debe ser diferente al número desde el que estás enviando")
                    print("   - Asegúrate de tener permisos de 'messaging' en el token")
                elif error.get('code') == 401:
                    print("\n   💡 El token ha expirado o es inválido. Genera uno nuevo en Meta Developers.")
                elif error.get('code') == 403:
                    print("\n   💡 No tienes permiso. Verifica los permisos del System User.")
        except:
            pass
        
except Exception as e:
    print(f"❌ Error de conexión: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("FIN DEL TEST")
print("=" * 70)
