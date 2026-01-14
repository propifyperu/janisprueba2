"""
Crear Emergency Address y asignarla a un IncomingPhoneNumber.
Ejecútalo localmente con tus credenciales en variables de entorno.

PowerShell ejemplo:
$env:TWILIO_ACCOUNT_SID='AC...'
$env:TWILIO_AUTH_TOKEN='TU_AUTH_TOKEN'
python scripts/twilio_create_emergency.py --sid PN60da1c645c8a580197c4f190c18a7f42 \
  --street "1600 Amphitheatre Pkwy" --city Mountain View --region CA --postal 94043 --country US --customer "Mi Empresa"

El script intentará crear la dirección y asignarla al número.
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
    parser = argparse.ArgumentParser(description='Crear Emergency Address en Twilio y asignar a IncomingPhoneNumber')
    parser.add_argument('--sid', required=True, help='IncomingPhoneNumber SID (PN...)')
    parser.add_argument('--street', required=True)
    parser.add_argument('--city', required=True)
    parser.add_argument('--region', required=True, help='State/Region code, e.g. CA')
    parser.add_argument('--postal', required=True, help='Postal code')
    parser.add_argument('--country', required=True, help='ISO country code, e.g. US')
    parser.add_argument('--customer', required=False, default='Client', help='Customer name for the address record')
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
        # Intentar crear una Emergency Address
        print('Creando Emergency Address...')
        addr = client.addresses.create(
            customer_name=args.customer,
            street=args.street,
            city=args.city,
            region=args.region,
            postal_code=args.postal,
            iso_country=args.country
        )
        print('Address creado:')
        print(json.dumps({'sid': addr.sid, 'url': getattr(addr, 'uri', None)}, indent=2))

        # Asignar al número
        print(f'Asignando address SID {addr.sid} al IncomingPhoneNumber {args.sid}...')
        updated = client.incoming_phone_numbers(args.sid).update(emergency_address_sid=addr.sid)
        print('Número actualizado:')
        print(json.dumps({'sid': getattr(updated, 'sid', None), 'phone_number': getattr(updated, 'phone_number', None), 'emergency_address_sid': getattr(updated, 'emergency_address_sid', None)}, indent=2))

    except Exception as e:
        print('Error al crear/assignar emergency address:', str(e))
        print('Si la operación no es soportada por tu cuenta, crea la dirección desde Twilio Console en Trust Hub -> Emergency Addresses y luego asigna al número.')


if __name__ == '__main__':
    main()
