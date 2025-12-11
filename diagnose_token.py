#!/usr/bin/env python
"""
Script para diagnosticar problemas con el token de WhatsApp
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
API_VERSION = 'v18.0'

print("=" * 70)
print("DIAGNÓSTICO DE TOKEN - WHATSAPP BUSINESS API")
print("=" * 70)

# Test 1: Validar el token accediendo a la info del usuario
print("\n1. Validando token con endpoint /me...")
try:
    url = f"https://graph.instagram.com/{API_VERSION}/me"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Token válido!")
        print(f"   Usuario ID: {data.get('id')}")
        print(f"   Nombre: {data.get('name')}")
    else:
        print(f"   ❌ Error: {response.text}")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 2: Obtener información del Business Account
print("\n2. Obteniendo información del Business Account...")
try:
    url = f"https://graph.instagram.com/{API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Business Account encontrado!")
        print(f"   Data: {data}")
    else:
        print(f"   ❌ Error: {response.text}")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 3: Obtener Phone Numbers
print("\n3. Listando teléfonos registrados en el Business Account...")
try:
    url = f"https://graph.instagram.com/{API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}/phone_numbers"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Teléfonos encontrados:")
        for phone in data.get('data', []):
            print(f"      - {phone.get('display_phone_number')} (ID: {phone.get('id')})")
    else:
        print(f"   ❌ Error: {response.text}")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 4: Obtener información del Phone Number
print("\n4. Verificando el Phone Number específico...")
try:
    url = f"https://graph.instagram.com/{API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Phone Number información:")
        print(f"      - Display: {data.get('display_phone_number')}")
        print(f"      - Status: {data.get('status')}")
        print(f"      - Data: {data}")
    else:
        print(f"   ❌ Error: {response.text}")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 70)
print("FIN DEL DIAGNÓSTICO")
print("=" * 70)
