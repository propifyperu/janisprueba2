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
    Procesa los mensajes del webhook
    """
    from properties.models import Lead, WhatsAppConversation, PropertyWhatsAppLink, LeadStatus
    
    messages = messages_data.get('messages', [])
    
    for message in messages:
        try:
            phone_number = message.get('from')
            message_id = message.get('id')
            timestamp = message.get('timestamp')
            
            # Obtener el tipo y contenido del mensaje
            message_type = message.get('type', 'text')  # text, image, video, document, audio
            
            if message_type == 'text':
                message_body = message.get('text', {}).get('body', '')
            else:
                message_body = f'[Mensaje de {message_type.upper()}]'
            
            # Buscar el tracking ID en los parámetros del contexto
            context = message.get('context', {})
            referred_product = context.get('referred_product')
            
            # Intentar obtener el link de WhatsApp mediante el ID de referencia
            whatsapp_link = None
            if referred_product:
                whatsapp_link = PropertyWhatsAppLink.objects.filter(
                    unique_identifier=referred_product
                ).first()
            
            # Obtener o crear el Lead
            if whatsapp_link:
                lead, created = Lead.objects.get_or_create(
                    phone_number=phone_number,
                    property=whatsapp_link.property,
                    defaults={
                        'whatsapp_link': whatsapp_link,
                        'social_network': whatsapp_link.social_network,
                        'status': LeadStatus.objects.filter(
                            property=whatsapp_link.property,
                            is_active=True
                        ).order_by('order').first()
                    }
                )
            else:
                # Sin link de rastreo, intentar encontrar por teléfono
                lead = Lead.objects.filter(phone_number=phone_number).first()
                if not lead:
                    logger.warning(f"Lead not found for phone {phone_number}")
                    return
            
            # Guardar el mensaje en la conversación
            WhatsAppConversation.objects.create(
                lead=lead,
                property=lead.property,
                message_type='incoming',
                sender_name=message.get('sender_name', phone_number),
                message_body=message_body,
                message_id=message_id,
            )
            
            # Actualizar last_message_at del lead
            from django.utils import timezone
            lead.last_message_at = timezone.now()
            lead.save()
            
            logger.info(f"Message processed for lead {phone_number}")
        
        except Exception as e:
            logger.error(f"Error processing message {message.get('id')}: {str(e)}")
            continue
