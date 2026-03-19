from django.db.models.signals import post_save, m2m_changed, pre_save
from properties.models import RequirementMatch
from notifications.events import on_property_matched
from django.dispatch import receiver
from django.core.cache import cache
import logging
from django.db import transaction
from .models import Property

from .models import Requirement, Event
from . import matching as matching_module

logger = logging.getLogger(__name__)

INACTIVE_AVAILABILITY = {"unavailable", "paused"}

@receiver(post_save, sender=Property)
def sync_is_active_with_availability(sender, instance: Property, **kwargs):
    should_be_active = instance.availability_status not in INACTIVE_AVAILABILITY
    if instance.is_active != should_be_active:
        Property.objects.filter(pk=instance.pk).update(is_active=should_be_active)

"""
@receiver(post_save, sender=Requirement)
def requirement_post_save_recalculate_matches(sender, instance: Requirement, created, **kwargs):
    Al guardar un Requirement, programar recálculo de coincidencias tras el commit.

    Usamos `transaction.on_commit` para garantizar que los cambios (incluyendo M2M)
    estén persistidos antes de ejecutar el motor de matching. Esto evita casos
    donde `post_save` se ejecuta antes de `form.save_m2m()` y los filtros quedan incompletos.
    
    try:
        req_id = instance.pk
        logger.debug('Requirement post_save schedule recalc for %s (created=%s)', req_id, bool(created))

        def _do_recalc():
            try:
                # Cargar instancia fresca
                req = Requirement.objects.filter(pk=req_id).first()
                if not req:
                    logger.debug('Requirement %s disappeared before recalc', req_id)
                    return

                matches = matching_module.get_matches_for_requirement(req, limit=10)
                cached = []
                for m in matches:
                    prop = m.get('property')
                    cached.append({
                        'property_id': getattr(prop, 'id', None),
                        'score': m.get('score'),
                        'details': m.get('details')
                    })
                cache_key = f'req_matches_{req.pk}'
                try:
                    cache.set(cache_key, cached, 60 * 60)
                except Exception:
                    logger.debug('Cache not available when setting matches for Requirement %s', req.pk)

                # notifications for owner
                try:
                    if cached and getattr(req, 'created_by', None):
                        user = req.created_by
                        notify_key = f'user_new_match_alerts_{user.id}'
                        notifications = []
                        for item in cached:
                            notifications.append({
                                'requirement_id': req.pk,
                                'property_id': item.get('property_id'),
                                'score': item.get('score'),
                            })
                        try:
                            cache.set(notify_key, notifications, 60 * 60 * 24)
                        except Exception:
                            logger.debug('Cache not available when setting match notifications for user %s', user.id)
                except Exception:
                    logger.exception('Error setting match notification for Requirement %s', req.pk)

                logger.debug('Recalc matches finished for Requirement %s, found %s', req.pk, len(cached))
            except Exception:
                logger.exception('Error recalculando matches para Requirement %s', req_id)

        try:
            transaction.on_commit(_do_recalc)
        except Exception:
            # Fallback immediate call if no transaction management available
            _do_recalc()
    except Exception:
        logger.exception('Failed scheduling recalc for Requirement %s', getattr(instance, 'pk', None))


# Manejar cambios en M2M para campos que afectan el matching
def _m2m_changed_handler(action, instance, **kwargs):
    # actions: 'post_add', 'post_remove', 'post_clear' son los relevantes
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    try:
        req_id = instance.pk
        logger.debug('M2M changed (%s) scheduling recalc for Requirement %s', action, req_id)

        def _do_recalc_m2m():
            try:
                req = Requirement.objects.filter(pk=req_id).first()
                if not req:
                    return
                matches = matching_module.get_matches_for_requirement(req, limit=10)
                cached = []
                for m in matches:
                    prop = m.get('property')
                    cached.append({
                        'property_id': getattr(prop, 'id', None),
                        'score': m.get('score'),
                        'details': m.get('details')
                    })
                cache_key = f'req_matches_{req.pk}'
                try:
                    cache.set(cache_key, cached, 60 * 60)
                except Exception:
                    logger.debug('Cache not available when setting matches for Requirement %s', req.pk)
            except Exception:
                logger.exception('Error in m2m recalc for Requirement %s', req_id)

        try:
            transaction.on_commit(_do_recalc_m2m)
        except Exception:
            _do_recalc_m2m()
    except Exception:
        logger.exception('Error handling m2m_changed for Requirement %s', getattr(instance, 'pk', None))


# conectar handlers para los through models de los M2M relevantes
try:
    m2m_changed.connect(lambda sender, instance, action, **kw: _m2m_changed_handler(action, instance, **kw), sender=Requirement.districts.through)
    m2m_changed.connect(lambda sender, instance, action, **kw: _m2m_changed_handler(action, instance, **kw), sender=Requirement.preferred_floors.through)
    m2m_changed.connect(lambda sender, instance, action, **kw: _m2m_changed_handler(action, instance, **kw), sender=Requirement.zonificaciones.through)
except Exception:
    logger.exception('Failed to connect m2m_changed handlers for Requirement')
"""
@receiver(post_save, sender=RequirementMatch)
def requirement_match_saved(sender, instance, created, **kwargs):
    # Solo dispara evento, nada más
    on_property_matched(instance)

@receiver(pre_save, sender=Event)
def capture_event_old_state(sender, instance, **kwargs): # Captura el estado anterior para detectar cambios de agente
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_assigned_agent = old.assigned_agent
        except sender.DoesNotExist:
            instance._old_assigned_agent = None
    else:
        instance._old_assigned_agent = None


@receiver(post_save, sender=Event)
def notify_agent_on_new_event(sender, instance, created, **kwargs): # Notifica al agente asignado cuando se crea una visita o se le asigna una existente.
    old_agent = getattr(instance, '_old_assigned_agent', None)

    event_agent = None
    if (created and instance.assigned_agent) or (instance.assigned_agent and instance.assigned_agent != old_agent):
        event_agent = instance.assigned_agent

    property_agents = set()
    if (created or instance.assigned_agent != old_agent) and instance.property:
        if getattr(instance.property, 'assigned_agent', None):
            property_agents.add(instance.property.assigned_agent)
        if getattr(instance.property, 'responsible', None):
            property_agents.add(instance.property.responsible)

    if event_agent in property_agents:
        event_agent = None

    all_targets = set(property_agents)
    if event_agent:
        all_targets.add(event_agent)

    if all_targets:
        try:
            from notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType
            from django.urls import reverse
            import threading
            import requests
            import os
            
            creator = instance.created_by
            prop_text = f"{instance.property.code}" if instance.property else "Sin propiedad"
            
            def _send_chatwoot_whatsapp(phone_number, payload_data, target_agent):
                phone_str = str(phone_number).strip()
                
                # 1. FORMATO DEL NÚMERO Y DATOS INICIALES
                if not phone_str.startswith('+'):
                    if phone_str.startswith('51') and len(phone_str) == 11:
                        phone_with_plus = '+' + phone_str
                    else:
                        phone_with_plus = '+51' + phone_str
                else:
                    phone_with_plus = phone_str
                    
                clean_source_id = phone_with_plus.replace('+', '')
                agent_name_str = target_agent.get_full_name() or target_agent.username if target_agent else "Agente Propify"

                user_token = os.getenv('CHATWOOT_USER_TOKEN', '6CFQrb6P4f7hfbZ6ieFsPzkr')
                bot_token = os.getenv('CHATWOOT_BOT_TOKEN', '6CFQrb6P4f7hfbZ6ieFsPzkr')
                
                if not user_token or not bot_token:
                    return

                user_headers = {
                    "Content-Type": "application/json",
                    "api_access_token": user_token 
                }
                
                bot_headers = {
                    "Content-Type": "application/json",
                    "api_access_token": bot_token 
                }
                
                base_url = "https://n8n-propify-chatwoot.qqaetr.easypanel.host/api/v1/accounts/2"
                
                try:
                    print(f"\n[CHATWOOT] === INICIANDO ENVÍO A {phone_with_plus} ===")
                    
                    # 2. BUSCAR / CREAR CONTACTO
                    search_url = f"{base_url}/contacts/search"
                    print(f"[CHATWOOT] Paso 1: GET {search_url} | params: {{'q': '{phone_with_plus}'}}")
                    search_response = requests.get(search_url, params={'q': phone_with_plus}, headers=user_headers)
                    print(f"[CHATWOOT] Paso 1 Respuesta ({search_response.status_code}): {search_response.text}")
                    
                    contact_id = None
                    if search_response.status_code in (200, 201):
                        search_payload = search_response.json().get('payload', [])
                        if search_payload:
                            contact_id = search_payload[0].get('id')
                            print(f"[CHATWOOT] Paso 1 Éxito -> contact_id encontrado: {contact_id}")
                            
                    if not contact_id:
                        create_contact_url = f"{base_url}/contacts"
                        contact_payload = {
                            "name": agent_name_str,
                            "phone_number": phone_with_plus
                        }
                        print(f"[CHATWOOT] Paso 1b: POST {create_contact_url} | payload: {contact_payload}")
                        create_response = requests.post(create_contact_url, json=contact_payload, headers=user_headers)
                        print(f"[CHATWOOT] Paso 1b Respuesta ({create_response.status_code}): {create_response.text}")
                        
                        if create_response.status_code in (200, 201):
                            contact_id = create_response.json().get('payload', {}).get('contact', {}).get('id')
                            print(f"[CHATWOOT] Paso 1b Éxito -> contact_id creado: {contact_id}")
                        else:
                            logger.error(f"Chatwoot Error creando contacto: {create_response.text}")
                            return
                            
                    if not contact_id:
                        logger.error("Chatwoot: No se pudo obtener ni crear el contact_id.")
                        return
                    
                    # 3. CREAR CONVERSACIÓN
                    conv_url = f"{base_url}/conversations"
                    conv_payload = {
                        "source_id": clean_source_id,
                        "contact_id": contact_id,
                        "inbox_id": 3
                    }
                    print(f"\n[CHATWOOT] Paso 2: POST {conv_url} | payload: {conv_payload}")
                    conv_response = requests.post(conv_url, json=conv_payload, headers=user_headers)
                    print(f"[CHATWOOT] Paso 2 Respuesta ({conv_response.status_code}): {conv_response.text}")
                    
                    conversation_id = None
                    if conv_response.status_code in (200, 201):
                        conversation_id = conv_response.json().get('id')
                        print(f"[CHATWOOT] Paso 2 Éxito -> conversation_id: {conversation_id}")
                    else:
                        logger.error(f"Chatwoot Paso 2 Error creando conversación: {conv_response.text}")
                        return
                        
                    if not conversation_id:
                        logger.error("Chatwoot: No se obtuvo el conversation_id.")
                        return
                    
                    # 4. ENVIAR MENSAJE
                    msg_url = f"{base_url}/conversations/{conversation_id}/messages"
                    print(f"\n[CHATWOOT] Paso 3: POST {msg_url}")
                    print(f"[CHATWOOT] Paso 3 Payload: {payload_data}")
                    msg_response = requests.post(msg_url, json=payload_data, headers=bot_headers)
                    print(f"[CHATWOOT] Paso 3 Respuesta ({msg_response.status_code}): {msg_response.text}")
                    
                    if msg_response.status_code not in (200, 201):
                        logger.error(f"Chatwoot Paso 3 Error: {msg_response.text}")
                        
                except Exception as e:
                    logger.error(f"Error enviando notificación Chatwoot a {phone_with_plus}: {e}")
                    print(f"[CHATWOOT] Error de Python: {e}")
                
                print("[CHATWOOT] === FIN DEL PROCESO ===\n")

            # Variables para la plantilla (comunes para todos los agentes)
            prop_title = instance.property.title if instance.property and instance.property.title else "Sin título"
            if len(prop_title) > 20:
                prop_title = prop_title[:20] + "..."
                
            prop_code = instance.property.code if instance.property and instance.property.code else "Sin código"
            event_code = instance.code or "Sin código"
            event_title = instance.titulo or "Sin título"
            
            combined_title = f"{event_title} - {prop_title}"
            
            months = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            if instance.fecha_evento:
                day = instance.fecha_evento.day
                month = months[instance.fecha_evento.month]
                year = instance.fecha_evento.year
                event_date = f"{day:02d} de {month} de {year}"
            else:
                event_date = "Fecha no especificada"

            event_time = f"{instance.hora_inicio.strftime('%H:%M')} - {instance.hora_fin.strftime('%H:%M')}" if instance.hora_inicio and instance.hora_fin else "Hora no especificada"
            
            if instance.contact:
                contact_name = instance.contact.full_name
            elif instance.interesado:
                contact_name = instance.interesado
            elif instance.lead:
                contact_name = instance.lead.full_name or instance.lead.username
            else:
                contact_name = "No especificado"

            # El nombre que va en el payload representa siempre al agente que dará la visita
            agent_name = instance.assigned_agent.get_full_name() or instance.assigned_agent.username if instance.assigned_agent else "Sin agente"
            creator_name = instance.created_by.get_full_name() or instance.created_by.username if instance.created_by else "Sistema"
            url = "https://propifai.com/dashboard/agenda/"

            # Enviar notificación y WhatsApp a TODOS los agentes en la lista
            for target_agent in all_targets:
                is_prop_agent = target_agent in property_agents

                if is_prop_agent or not instance.property:
                    notif_message = f"Se ha solicitado una visita para tu propiedad el {instance.fecha_evento} a las {instance.hora_inicio}. Propiedad: {prop_text}. Título: {instance.titulo}" if is_prop_agent else f"Se te ha asignado un evento el {instance.fecha_evento} a las {instance.hora_inicio}. Título: {instance.titulo}"
                    notif_data = {
                        "event_code": instance.code,
                        "actions": [
                            {"label": "Aceptar", "url": reverse('properties:event_accept', args=[instance.id]), "method": "POST"},
                            {"label": "Rechazar", "url": reverse('properties:event_reject', args=[instance.id]), "method": "POST"}
                        ]
                    }
                    template_name = "solicitud_de_visita_agentes_oficial"
                else:
                    notif_message = f"Se te ha asignado una visita el {instance.fecha_evento} a las {instance.hora_inicio}. Propiedad: {prop_text}. Título: {instance.titulo}"
                    notif_data = {
                        "event_code": instance.code
                    }
                    template_name = "solicitud_de_visita_agentes"

                # 1. Notificación en plataforma
                Notification.objects.create(
                    user=target_agent,
                    event_type="EVENT_ASSIGNED",
                    title=f"Nueva Visita: {instance.code}",
                    message=notif_message,
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=instance.id,
                    data=notif_data
                )

                # 2. WhatsApp vía Chatwoot
                if getattr(target_agent, 'phone', None):
                    payload = {
                        "content": "🔰 SOLICITUD DE VISITA (PROPIFY)",
                        "message_type": "outgoing",
                        "content_type": "text",
                        "private": False,
                        "template_params": {
                            "name": template_name,
                            "category": "UTILITY",
                            "language": "es_PE",
                            "processed_params": {
                                "body": {
                                    "1": combined_title,
                                    "2": event_code,
                                    "3": event_date,
                                    "4": event_time,
                                    "5": prop_code,
                                    "6": creator_name,
                                    "7": agent_name,
                                    "8": contact_name,
                                    "9": url,
                                }
                            }
                        }
                    }
                    threading.Thread(target=_send_chatwoot_whatsapp, args=(target_agent.phone, payload, target_agent)).start()

        except Exception as e:
            logger.exception(f"Error generando notificación de visita para evento {instance.id}")

@receiver(post_save, sender=Event)
def update_event_notifications_on_status_change(sender, instance, **kwargs):
    try:
        if instance.status != sender.STATUS_PENDING:
            from notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType
            ctype = ContentType.objects.get_for_model(instance)
            notifs = Notification.objects.filter(content_type=ctype, object_id=instance.id)
            for n in notifs:
                if isinstance(n.data, dict) and 'actions' in n.data:
                    n.data.pop('actions', None)
                    n.data['status'] = instance.status
                    n.data['status_display'] = instance.get_status_display()
                    n.save(update_fields=['data'])
    except Exception:
        pass