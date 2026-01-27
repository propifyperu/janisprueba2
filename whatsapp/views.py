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


def process_messages(messages_data):
    """
    Procesa los mensajes del webhook con una lógica de tracking robusta.
    """
    from properties.models import Lead, WhatsAppConversation, PropertyWhatsAppLink, LeadStatus
    import re

    # 1. Obtener todos los identificadores únicos activos para una búsqueda eficiente.
    # Esto es mucho más robusto que depender de un regex.
    active_identifiers = set(PropertyWhatsAppLink.objects.filter(is_active=True).values_list('unique_identifier', flat=True))
    
    if not active_identifiers:
        logger.warning("[TRACKING] No hay identificadores únicos activos en la base de datos. El tracking no funcionará.")
        # No es necesario salir, podría haber leads existentes sin tracking.
    
    for message in messages:
        message_id = message.get('id')
        try:
            phone_number = message.get('from')
            message_body = ""
            whatsapp_link = None
            
            # 2. Extraer contenido y buscar el tracking_id de forma fiable
            message_type = message.get('type', 'text')
            if message_type == 'text':
                message_body = message.get('text', {}).get('body', '')
                # Extraer todas las "palabras" del mensaje
                words_in_message = set(re.findall(r'\b[\w\-]+\b', message_body))
                # Encontrar la intersección entre las palabras del mensaje y nuestros códigos
                found_identifiers = words_in_message.intersection(active_identifiers)
                
                if found_identifiers:
                    found_id = found_identifiers.pop()
                    logger.info(f"[TRACKING] ¡ÉXITO! Identificador '{found_id}' encontrado en el mensaje de {phone_number}.")
                    whatsapp_link = PropertyWhatsAppLink.objects.get(unique_identifier=found_id)
                else:
                    logger.warning(f"[TRACKING] No se encontró un identificador de tracking válido en el mensaje de {phone_number}: '{message_body}'")
            else:
                message_body = f'[{message_type.upper()}]'

            # 3. Lógica de guardado explícita y segura
            lead = None
            if whatsapp_link:
                # Si encontramos un link, buscamos o creamos el Lead asociado a ESA propiedad.
                lead, created = Lead.objects.get_or_create(
                    phone_number=phone_number,
                    property=whatsapp_link.property,
                    defaults={
                        'whatsapp_link': whatsapp_link,
                        'social_network': whatsapp_link.social_network,
                        'status': LeadStatus.objects.filter(property=whatsapp_link.property, is_active=True).order_by('order').first()
                    }
                )
                
                if created:
                    logger.info(f"[DB] Lead CREADO (ID: {lead.id}) para {phone_number} con whatsapp_link_id: {whatsapp_link.id}")
                else:
                    logger.info(f"[DB] Lead ENCONTRADO (ID: {lead.id}) para {phone_number}.")
                    # Si el lead ya existía, nos aseguramos de que tenga el link correcto.
                    if lead.whatsapp_link != whatsapp_link:
                        lead.whatsapp_link = whatsapp_link
                        lead.save(update_fields=['whatsapp_link', 'updated_at'])
                        logger.info(f"[DB] Lead (ID: {lead.id}) ACTUALIZADO con el whatsapp_link_id: {whatsapp_link.id}")

            else:
                # Si NO hay tracking, buscamos el lead más reciente para ese número.
                lead = Lead.objects.filter(phone_number=phone_number).order_by('-created_at').first()
                if not lead:
                    logger.error(f"CRÍTICO: No se pudo trackear y no existe lead previo para {phone_number}. Se ignora el mensaje.")
                    continue # No podemos hacer nada con este mensaje, pasamos al siguiente.

            # 4. Guardar la conversación y actualizar el timestamp del lead
            WhatsAppConversation.objects.create(
                lead=lead,
                property=lead.property,
                message_type='incoming',
                sender_name=message.get('sender_name', phone_number),
                message_body=message_body,
                message_id=message_id,
            )
            
            from django.utils import timezone
            lead.last_message_at = timezone.now()
            lead.save(update_fields=['last_message_at', 'updated_at'])

            logger.info(f"PROCESO COMPLETO: Mensaje de {phone_number} guardado para Lead ID: {lead.id}")

        except Exception as e:
            logger.error(f"Error fatal procesando mensaje (ID: {message_id}): {str(e)}", exc_info=True)
            continue


@csrf_exempt
def twilio_webhook(request):
    """Handler para webhooks desde Twilio (WhatsApp Sandbox o número Twilio).

    Espera POST form-encoded con campos como `From`, `To`, `Body`, `NumMedia`, `MediaUrl0`, `MessageSid`.
    """
    from properties.models import Lead, WhatsAppConversation, PropertyWhatsAppLink, LeadStatus
    import re
    from django.utils import timezone

    # Validar firma opcional (recomendado en producción)
    # Instrumentación temporal: loguear META, POST y body para diagnóstico
    try:
        logger.info('Twilio webhook META: %s', {k: request.META.get(k) for k in ['HTTP_HOST', 'HTTP_X_TWILIO_SIGNATURE', 'X-Forwarded-For', 'REMOTE_ADDR']})
        try:
            post_dict = request.POST.dict()
        except Exception:
            post_dict = str(request.POST)
        logger.info('Twilio webhook POST data: %s', post_dict)
        logger.info('Twilio webhook raw body length: %s', len(request.body or b''))
    except Exception:
        logger.exception('Failed to log incoming Twilio request')

    # Persistir evidencia del request a un archivo para depuración externa (ngrok/Twilio)
    try:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, 'twilio_requests.log')
        with open(log_file, 'a', encoding='utf-8') as fh:
            fh.write('--- TWILIO REQUEST %s ---\n' % datetime.utcnow().isoformat())
            # Basic META subset
            for k in ['HTTP_HOST', 'HTTP_X_TWILIO_SIGNATURE', 'X-Forwarded-For', 'REMOTE_ADDR', 'REQUEST_METHOD', 'PATH_INFO']:
                fh.write(f"{k}: {request.META.get(k)}\n")
            try:
                post_dict = request.POST.dict()
            except Exception:
                post_dict = str(request.POST)
            fh.write('POST: ' + json.dumps(post_dict, ensure_ascii=False) + '\n')
            fh.write('RAW_BODY_LEN: %s\n' % (len(request.body or b'')))
            fh.write('--- END ---\n\n')
    except Exception:
        logger.exception('Failed to write Twilio request to file')

    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    signature = request.META.get('HTTP_X_TWILIO_SIGNATURE')
    if auth_token and signature and RequestValidator is not None:
        validator = RequestValidator(auth_token)
        url = request.build_absolute_uri()
        params = request.POST.dict()
        valid = validator.validate(url, params, signature)
        if not valid:
            logger.warning('Twilio signature validation failed')
            return JsonResponse({'error': 'invalid signature'}, status=403)
    else:
        logger.debug('Twilio signature validation skipped (no auth token or RequestValidator available)')

    try:
        from django.db import transaction

        with transaction.atomic():
            frm = request.POST.get('From', '')  # formato: whatsapp:+1234...
            to = request.POST.get('To', '')
            body = request.POST.get('Body', '') or ''
            message_sid = request.POST.get('MessageSid') or request.POST.get('SmsSid')
            num_media = int(request.POST.get('NumMedia', '0') or 0)
            media_url = None
            media_type = None
            if num_media > 0:
                media_url = request.POST.get('MediaUrl0')
                media_type = request.POST.get('MediaContentType0')

            phone_number = frm.replace('whatsapp:', '') if frm else ''

            # Tracking: intentar encontrar unique_identifier en el cuerpo
            active_identifiers = set(PropertyWhatsAppLink.objects.filter(is_active=True).values_list('unique_identifier', flat=True))
            found_identifier = None
            if body:
                words = set(re.findall(r'\b[\w\-]+\b', body))
                inter = words.intersection(active_identifiers)
                if inter:
                    found_identifier = inter.pop()

            whatsapp_link = None
            lead = None
            if found_identifier:
                try:
                    whatsapp_link = PropertyWhatsAppLink.objects.get(unique_identifier=found_identifier)
                except PropertyWhatsAppLink.DoesNotExist:
                    whatsapp_link = None

            if whatsapp_link:
                lead, created = Lead.objects.get_or_create(
                    phone_number=phone_number,
                    property=whatsapp_link.property,
                    defaults={
                        'whatsapp_link': whatsapp_link,
                        'social_network': whatsapp_link.social_network,
                        'status': LeadStatus.objects.filter(property=whatsapp_link.property, is_active=True).order_by('order').first()
                    }
                )
                if not created and lead.whatsapp_link != whatsapp_link:
                    lead.whatsapp_link = whatsapp_link
                    lead.save(update_fields=['whatsapp_link', 'updated_at'])
            else:
                lead = Lead.objects.filter(phone_number=phone_number).order_by('-created_at').first()
                if not lead:
                    # crear lead sin propiedad conocida: intentar usar valores configurados en settings
                    from properties.models import Property, SocialNetwork
                    default_property = None
                    default_social = None

                    # Preferir IDs configurados explícitamente en settings
                    try:
                        default_prop_id = int(getattr(settings, 'WHATSAPP_DEFAULT_PROPERTY_ID') or 0)
                    except Exception:
                        default_prop_id = 0

                    try:
                        default_social_id = int(getattr(settings, 'WHATSAPP_DEFAULT_SOCIAL_ID') or 0)
                    except Exception:
                        default_social_id = 0

                    if default_prop_id:
                        default_property = Property.objects.filter(pk=default_prop_id).first()
                        if not default_property:
                            logger.error(f"WHATSAPP_DEFAULT_PROPERTY_ID={default_prop_id} no encontrado en la base de datos")
                            raise Exception('configured default property not found')
                    else:
                        default_property = Property.objects.first()

                    # Determinar social_network preferente
                    if default_social_id:
                        default_social = SocialNetwork.objects.filter(pk=default_social_id).first()
                        if not default_social:
                            logger.error(f"WHATSAPP_DEFAULT_SOCIAL_ID={default_social_id} no encontrado en la base de datos")
                            raise Exception('configured default social_network not found')
                    else:
                        if PropertyWhatsAppLink.objects.exists():
                            default_social = PropertyWhatsAppLink.objects.first().social_network
                        else:
                            default_social = SocialNetwork.objects.first()

                    if default_property is None:
                        # No podemos insertar un Lead sin property (constraint DB); registrar y abortar la operación
                        logger.error('No existe ninguna `Property` en la base de datos para asignar al Lead. No se crea el Lead.')
                        raise Exception('no default property to assign lead')

                    if default_social is None:
                        logger.error('No existe SocialNetwork para asignar al Lead. No se crea el Lead.')
                        raise Exception('no default social_network to assign lead')

                    lead = Lead.objects.create(
                        phone_number=phone_number,
                        name=None,
                        social_network=default_social,
                        property=default_property
                    )

            # Evitar insertar duplicados por message_id (constraint UNIQUE)
            existing_conv = None
            if message_sid:
                existing_conv = WhatsAppConversation.objects.filter(message_id=message_sid).first()

            if existing_conv:
                logger.info(f"Twilio: conversación con message_id {message_sid} ya existe (id={existing_conv.id}), se omite la creación.")
                # Actualizar timestamp del lead asociado a la conversación existente
                try:
                    existing_lead = existing_conv.lead
                    existing_lead.last_message_at = timezone.now()
                    existing_lead.save(update_fields=['last_message_at', 'updated_at'])
                except Exception:
                    logger.exception('No se pudo actualizar last_message_at del lead existente')
            else:
                # Crear nueva conversación si no existe message_id previo
                WhatsAppConversation.objects.create(
                    lead=lead,
                    property=lead.property if getattr(lead, 'property', None) else (whatsapp_link.property if whatsapp_link else None),
                    message_type='incoming',
                    sender_name=request.POST.get('ProfileName') or phone_number,
                    message_body=body or (media_type or '[MEDIA]'),
                    message_id=message_sid,
                    media_url=media_url,
                    media_type=media_type,
                )

                lead.last_message_at = timezone.now()
                lead.save(update_fields=['last_message_at', 'updated_at'])

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        logger.exception('Error procesando webhook Twilio: %s', str(e))
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
