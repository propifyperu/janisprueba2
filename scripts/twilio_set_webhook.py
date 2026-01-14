"""
Actualizar el webhook (SmsUrl) de un IncomingPhoneNumber.
Usa variables de entorno TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN.

Ejemplo PowerShell:
$env:TWILIO_ACCOUNT_SID='AC...'
$env:TWILIO_AUTH_TOKEN='TU_AUTH_TOKEN'
python scripts/twilio_set_webhook.py --sid PN60da1c645c8a580197c4f190c18a7f42 --sms_url "https://abcd.ngrok.io/whatsapp/twilio/"
"""

import os
import sys
import argparse
import json

try:
    from twilio.rest import Client
except Exception:
    Client = None


def main():
    parser = argparse.ArgumentParser(description='Actualizar SmsUrl (webhook) de un IncomingPhoneNumber en Twilio')
    parser.add_argument('--sid', required=True, help='IncomingPhoneNumber SID (PN...)')
    parser.add_argument('--sms_url', required=True, help='URL pública HTTPS que recibirá webhooks de mensajes entrantes')
    args = parser.parse_args()

    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')

    if not sid or not token:
        print('ERROR: configura TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN como variables de entorno antes de ejecutar.')
        sys.exit(1)

    if Client is None:
        print('ERROR: instala la librería twilio: pip install twilio')
        sys.exit(1)

    client = Client(sid, token)

    try:
        print(f'Actualizando SmsUrl de {args.sid} a {args.sms_url} ...')
        updated = client.incoming_phone_numbers(args.sid).update(sms_url=args.sms_url)
        print('Número actualizado:')
        print(json.dumps({'sid': getattr(updated, 'sid', None), 'phone_number': getattr(updated, 'phone_number', None), 'sms_url': getattr(updated, 'sms_url', None)}, indent=2))
    except Exception as e:
        print('Error actualizando webhook:', str(e))


if __name__ == '__main__':
    main()
