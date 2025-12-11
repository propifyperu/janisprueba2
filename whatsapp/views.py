from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging

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
