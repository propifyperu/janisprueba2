#!/usr/bin/env python
"""
Script para probar la conexión con WhatsApp Business API
"""
import os
import sys
import django
import requests
from dotenv import load_dotenv

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

load_dotenv()

# Obtener credenciales
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
API_VERSION = 'v18.0'

print("=" * 60)
print("TEST DE CONEXIÓN - WHATSAPP BUSINESS API")
print("=" * 60)

# Test 1: Verificar credenciales
print("\n1. Verificando credenciales...")
if not WHATSAPP_ACCESS_TOKEN:
    print("❌ WHATSAPP_ACCESS_TOKEN no configurado")
else:
    token_preview = WHATSAPP_ACCESS_TOKEN[:20] + "..." + WHATSAPP_ACCESS_TOKEN[-10:]
    print(f"✅ Token cargado: {token_preview}")

if not WHATSAPP_PHONE_NUMBER_ID:
    print("❌ WHATSAPP_PHONE_NUMBER_ID no configurado")
else:
    print(f"✅ Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")

if not WHATSAPP_BUSINESS_ACCOUNT_ID:
    print("❌ WHATSAPP_BUSINESS_ACCOUNT_ID no configurado")
else:
    print(f"✅ Business Account ID: {WHATSAPP_BUSINESS_ACCOUNT_ID}")

# Test 2: Probar conexión con la API
print("\n2. Probando conexión con Meta Graph API...")
try:
    # Endpoint para obtener información del Business Account
    url = f"https://graph.instagram.com/{API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Conexión exitosa!")
        data = response.json()
        print(f"   Business Account Details: {data}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error de conexión: {str(e)}")

# Test 3: Obtener Phone Numbers registrados
if WHATSAPP_PHONE_NUMBER_ID:
    print("\n3. Obteniendo números de teléfono registrados...")
    try:
        url = f"https://graph.instagram.com/{API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}/phone_numbers"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ Números registrados:")
            data = response.json()
            for number in data.get('data', []):
                print(f"   - {number.get('display_phone_number')} (ID: {number.get('id')})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)
