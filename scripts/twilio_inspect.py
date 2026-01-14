"""
Script de inspección de Twilio (ejecutar localmente).
- Recolecta Incoming Phone Numbers, SIDs y URLs de webhook.
- Recolecta Messaging Services y sus configuraciones.

INSTRUCCIONES:
1) Instala dependencias: pip install twilio
2) Exporta variables de entorno (PowerShell ejemplo):
   $env:TWILIO_ACCOUNT_SID="AC..."
   $env:TWILIO_AUTH_TOKEN="your_auth_token"
3) Ejecuta: python scripts/twilio_inspect.py

Nota: Este script no envía tus credenciales a nadie: todo se ejecuta localmente.
"""

import os
import sys
import json
from typing import Any

try:
    from twilio.rest import Client
except Exception:
    Client = None


def safe_print(title: str, data: Any):
    print('\n' + '=' * 60)
    print(title)
    print('-' * 60)
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(data)


def main():
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')

    if not sid or not token:
        print('ERROR: configura las variables de entorno TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN antes de ejecutar.')
        print('En PowerShell ejemplo:')
        print('  $env:TWILIO_ACCOUNT_SID="AC..."')
        print('  $env:TWILIO_AUTH_TOKEN="your_auth_token"')
        sys.exit(1)

    if Client is None:
        print('ERROR: falta la librería twilio. Instala con: pip install twilio')
        sys.exit(1)

    client = Client(sid, token)

    # Account info (no imprime token)
    safe_print('Account SID', {'account_sid': sid})

    # Incoming Phone Numbers
    try:
        incoming = client.incoming_phone_numbers.list(limit=100)
        numbers = []
        for num in incoming:
            info = {
                'sid': getattr(num, 'sid', None),
                'phone_number': getattr(num, 'phone_number', None),
                'friendly_name': getattr(num, 'friendly_name', None),
                'voice_url': getattr(num, 'voice_url', None),
                'voice_method': getattr(num, 'voice_method', None),
                'sms_url': getattr(num, 'sms_url', None) if hasattr(num, 'sms_url') else getattr(num, 'sms_url', None),
                'sms_method': getattr(num, 'sms_method', None) if hasattr(num, 'sms_method') else getattr(num, 'sms_method', None),
                'emergency_address_sid': getattr(num, 'emergency_address_sid', None) if hasattr(num, 'emergency_address_sid') else None,
                'status_callback': getattr(num, 'status_callback', None) if hasattr(num, 'status_callback') else None,
            }
            numbers.append(info)
        safe_print('Incoming Phone Numbers', numbers)
    except Exception as e:
        safe_print('Error listing incoming phone numbers', str(e))

    # Messaging Services
    try:
        services = client.messaging.services.list(limit=100)
        svc_list = []
        for svc in services:
            svc_info = {
                'sid': getattr(svc, 'sid', None),
                'friendly_name': getattr(svc, 'friendly_name', None),
                'inbound_request_url': getattr(svc, 'inbound_request_url', None) if hasattr(svc, 'inbound_request_url') else getattr(svc, 'inbound_webhook_url', None),
                'fallback_url': getattr(svc, 'fallback_url', None) if hasattr(svc, 'fallback_url') else None,
                'sticky_sender': getattr(svc, 'sticky_sender', None) if hasattr(svc, 'sticky_sender') else None,
            }
            svc_list.append(svc_info)
        safe_print('Messaging Services', svc_list)
    except Exception as e:
        safe_print('Error listing messaging services', str(e))

    # API Keys (list limited info)
    try:
        keys = client.new_keys.list() if hasattr(client, 'new_keys') else None
        keys_out = []
        if keys:
            for k in keys:
                keys_out.append({'sid': getattr(k, 'sid', None), 'friendly_name': getattr(k, 'friendly_name', None)})
        else:
            # fallback: check client.api.keys
            try:
                api_keys = client.api.keys.list()
                for k in api_keys:
                    keys_out.append({'sid': getattr(k, 'sid', None), 'friendly_name': getattr(k, 'friendly_name', None)})
            except Exception:
                keys_out = 'not available or insufficient permissions'
        safe_print('API Keys', keys_out)
    except Exception as e:
        safe_print('Error listing API keys', str(e))

    # Basic help: curl commands to update webhook on incoming phone number
    example_update = (
        "curl -X POST 'https://api.twilio.com/2010-04-01/Accounts/%s/IncomingPhoneNumbers/{INCOMING_SID}.json' "
        "--data-urlencode 'SmsUrl=https://your-public-url/whatsapp/twilio/' "
        "-u %s:YOUR_AUTH_TOKEN"
    ) % (sid, sid)

    safe_print('Examples', {
        'set_incoming_number_sms_webhook_curl_example': example_update,
        'note': 'Reemplaza {INCOMING_SID} por el SID del número que quieras actualizar. NO compartas tu AUTH TOKEN en foros públicos.'
    })

    print('\nInspección completa.')


if __name__ == '__main__':
    main()
