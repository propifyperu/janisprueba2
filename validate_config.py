#!/usr/bin/env python
"""
Script simple para validar la configuración de WhatsApp
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("VALIDACIÓN DE CONFIGURACIÓN - WHATSAPP BUSINESS API")
print("=" * 70)

# Verificar credenciales
token = os.getenv('WHATSAPP_ACCESS_TOKEN', '').strip()
phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '').strip()
business_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', '').strip()
verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', '').strip()

print("\n1. Verificando archivo .env:\n")

print(f"WHATSAPP_ACCESS_TOKEN:")
if token:
    print(f"  ✅ Configurado (longitud: {len(token)} caracteres)")
    print(f"  Primeros 30 chars: {token[:30]}")
    print(f"  Últimos 10 chars: {token[-10:]}")
else:
    print(f"  ❌ NO CONFIGURADO")

print(f"\nWHATSAPP_PHONE_NUMBER_ID:")
if phone_id:
    print(f"  ✅ Configurado: {phone_id}")
else:
    print(f"  ❌ NO CONFIGURADO")

print(f"\nWHATSAPP_BUSINESS_ACCOUNT_ID:")
if business_id:
    print(f"  ✅ Configurado: {business_id}")
else:
    print(f"  ❌ NO CONFIGURADO")

print(f"\nWHATSAPP_VERIFY_TOKEN:")
if verify_token:
    print(f"  ✅ Configurado: {verify_token}")
else:
    print(f"  ❌ NO CONFIGURADO")

# Detectar problemas comunes
print("\n2. Validando formato:\n")

if token and ' ' in token:
    print("  ⚠️  El token contiene espacios (podría causar error)")
if token and len(token) < 100:
    print("  ⚠️  El token parece muy corto (debería tener ~200+ caracteres)")
if phone_id and not phone_id.isdigit():
    print(f"  ⚠️  El Phone Number ID contiene caracteres no numéricos")
if business_id and not business_id.isdigit():
    print(f"  ⚠️  El Business Account ID contiene caracteres no numéricos")

print("\n" + "=" * 70)
