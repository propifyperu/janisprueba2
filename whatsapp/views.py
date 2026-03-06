from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests
import mimetypes
from urllib.parse import urlparse


# Minimal Twilio MMS handler based on Twilio docs.
# - Saves any MediaUrlX attachments to MEDIA_ROOT/whatsapp/
# - Returns simple TwiML confirmation


@csrf_exempt
def twilio_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'only POST'}, status=405)

    # Extract basic fields
    from_number = request.POST.get('From', '')
    message_sid = request.POST.get('MessageSid', '')
    num_media = int(request.POST.get('NumMedia', '0') or 0)
    body = request.POST.get('Body', '')

    saved_files = []

    media_dir = os.path.join(settings.MEDIA_ROOT, 'whatsapp')
    os.makedirs(media_dir, exist_ok=True)

    for i in range(num_media):
        media_url = request.POST.get(f'MediaUrl{i}')
        media_content_type = request.POST.get(f'MediaContentType{i}', '')
        if not media_url:
            continue

        # Attempt download
        try:
            resp = requests.get(media_url, timeout=15)
            resp.raise_for_status()
            parsed = urlparse(media_url)
            media_sid = os.path.basename(parsed.path)
            # Guess extension from content-type
            ext = mimetypes.guess_extension(media_content_type.split(';')[0].strip() or '') or ''
            filename = f"{message_sid or media_sid}{ext}"
            path = os.path.join(media_dir, filename)
            with open(path, 'wb') as fh:
                fh.write(resp.content)
            saved_files.append(filename)
        except Exception:
            # skip failed media downloads
            continue

    # Simple TwiML reply so Twilio knows we processed the webhook
    resp = MessagingResponse()
    if num_media:
        resp.message(f"Recibido {num_media} archivo(s). Gracias!")
    else:
        resp.message("Recibido. Gracias!")

    return HttpResponse(str(resp), content_type='application/xml')
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging
from typing import Dict, Any
from datetime import datetime
import os

try:
    from twilio.rest import Client
    from twilio.request_validator import RequestValidator
except Exception:
    Client = None
    RequestValidator = None

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    Webhook para recibir y procesar mensajes de WhatsApp Business API
    """
    if request.method == "GET":
        return handle_webhook_verification(request)
    elif request.method == "POST":
        return handle_webhook_message(request)


def handle_webhook_verification(request):
    """
    Meta envía un GET request para verificar el webhook
    Debe responder con el parámetro challenge
    """
    verify_token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    # Verificar que el token sea correcto
    if verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return JsonResponse({'hub.challenge': challenge}, safe=False)
    else:
        logger.warning(f"Webhook verification failed: invalid token {verify_token}")
        return JsonResponse({'error': 'Invalid verification token'}, status=403)


def handle_webhook_message(request):
    """
    Procesa los mensajes entrantes de WhatsApp
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Webhook received: {data}")
        
        # Estructura típica de Meta
        if data.get('object') == 'whatsapp_business_account':
            entries = data.get('entry', [])
            
            for entry in entries:
                changes = entry.get('changes', [])
                
                for change in changes:
                    if change.get('field') == 'messages':
                        messages_data = change.get('value', {})
                        process_messages(messages_data)
        
        return JsonResponse({'status': 'ok'})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def send_whatsapp_message(to_number: str, body: str = None, media_url: str = None) -> Dict[str, Any]:
    """Enviar mensaje WhatsApp usando Twilio REST API.

    `to_number` debe ser en formato E.164 con código de país (ej. +519XXXXXXXX).
    Retorna el dict con respuesta del API o error.
    """
    if Client is None:
        logger.error('Twilio Client no está disponible. Instala la dependencia `twilio`.')
        return {'error': 'twilio not installed'}

    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_whatsapp = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)

    if not all([sid, token, from_whatsapp]):
        logger.error('Faltan credenciales TWILIO: revisa TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_NUMBER en settings.')
        return {'error': 'missing credentials'}

    client = Client(sid, token)
    to_whatsapp = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number

    try:
        if media_url:
            msg = client.messages.create(body=body or '', from_=from_whatsapp, to=to_whatsapp, media_url=[media_url])
        else:
            msg = client.messages.create(body=body or '', from_=from_whatsapp, to=to_whatsapp)
        logger.info(f'Message sent via Twilio: SID={getattr(msg, "sid", None)}')
        return {'sid': getattr(msg, 'sid', None), 'status': getattr(msg, 'status', None)}
    except Exception as e:
        logger.exception('Error sending message via Twilio: %s', str(e))
        return {'error': str(e)}
