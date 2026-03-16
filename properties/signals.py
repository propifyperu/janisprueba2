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
    agent = instance.assigned_agent

    should_notify = (created and agent) or (agent and agent != old_agent)

    if should_notify:
        try:
            from notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType
            from django.urls import reverse
            
            creator = instance.created_by

            prop_text = f"{instance.property.code}" if instance.property else "Sin propiedad"
            
            message_text = (
                f"Se te ha asignado una visita el {instance.fecha_evento} a las {instance.hora_inicio}. "
                f"Propiedad: {prop_text}. Título: {instance.titulo}"
            )
            
            Notification.objects.create(
                user=agent,
                event_type="EVENT_ASSIGNED",
                title=f"Nueva Visita: {instance.code}",
                message=message_text,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                data={
                    "event_code": instance.code,
                    "actions": [
                        {"label": "Aceptar", "url": reverse('properties:event_accept', args=[instance.id]), "method": "POST"},
                        {"label": "Rechazar", "url": reverse('properties:event_reject', args=[instance.id]), "method": "POST"}
                    ]
                }
            )
            
            # --- ENVÍO DE MENSAJE WHATSAPP (CHATWOOT) ---
            if getattr(agent, 'phone', None):
                import threading
                import requests
                import os
                
                def _send_chatwoot_whatsapp(phone_number, msg_content):
                    phone_str = str(phone_number).strip()
                    
                    # Validación para asegurar que tenga el prefijo +51
                    if not phone_str.startswith('+'):
                        if phone_str.startswith('51') and len(phone_str) == 11:
                            phone_str = '+' + phone_str
                        else:
                            phone_str = '+51' + phone_str

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
                        print(f"\n[CHATWOOT] === INICIANDO ENVÍO A {phone_str} ===")
                        
                        # Paso 1: Buscar Contacto
                        search_url = f"{base_url}/contacts/search"
                        # Pasamos la variable por 'params' para que request codifique el '+' a '%2B' correctamente
                        print(f"[CHATWOOT] Paso 1: GET {search_url} | params: {{'q': '{phone_str}'}}")
                        search_response = requests.get(search_url, params={'q': phone_str}, headers=user_headers)
                        print(f"[CHATWOOT] Paso 1 Respuesta ({search_response.status_code}): {search_response.text}")
                        
                        if search_response.status_code not in (200, 201): 
                            logger.error(f"Chatwoot Paso 1 Error: {search_response.text}")
                            return
                        search_payload = search_response.json().get('payload', [])
                        if not search_payload: 
                            logger.warning(f"Chatwoot Paso 1: No se encontró contacto para {phone_str}")
                            return
                        contact_id = search_payload[0].get('id')
                        print(f"[CHATWOOT] Paso 1 Éxito -> contact_id: {contact_id}")
                        
                        # Paso 2: Buscar Conversación
                        conv_url = f"{base_url}/contacts/{contact_id}/conversations"
                        print(f"\n[CHATWOOT] Paso 2: GET {conv_url}")
                        conv_response = requests.get(conv_url, headers=user_headers)
                        print(f"[CHATWOOT] Paso 2 Respuesta ({conv_response.status_code}): {conv_response.text}")
                        
                        if conv_response.status_code not in (200, 201): 
                            logger.error(f"Chatwoot Paso 2 Error: {conv_response.text}")
                            return
                        conv_payload = conv_response.json().get('payload', [])
                        if not conv_payload: 
                            logger.warning(f"Chatwoot Paso 2: El contacto {phone_str} no tiene conversaciones activas.")
                            return
                        conversation_id = conv_payload[0].get('id')
                        print(f"[CHATWOOT] Paso 2 Éxito -> conversation_id: {conversation_id}")
                        
                        # Paso 3: Enviar Mensaje
                        msg_url = f"{base_url}/conversations/{conversation_id}/messages"
                        payload = {
                            "content": msg_content,
                            "message_type": "outgoing",
                            "content_type": "text",
                            "private": False
                        }
                        print(f"\n[CHATWOOT] Paso 3: POST {msg_url}")
                        print(f"[CHATWOOT] Paso 3 Payload: {payload}")
                        msg_response = requests.post(msg_url, json=payload, headers=bot_headers)
                        print(f"[CHATWOOT] Paso 3 Respuesta ({msg_response.status_code}): {msg_response.text}")
                        
                        if msg_response.status_code not in (200, 201):
                            logger.error(f"Chatwoot Paso 3 Error: {msg_response.text}")
                            
                    except Exception as e:
                        logger.error(f"Error enviando notificación Chatwoot: {e}")
                        print(f"[CHATWOOT] Error de Python: {e}")
                    
                    print("[CHATWOOT] === FIN DEL PROCESO ===\n")

                prop_code = f"{instance.property.code}" if instance.property else "Sin propiedad vinculada"
                custom_message = (
                    f"📅 *Nuevo Evento Asignado*\n\n"
                    f"📌 *Título:* {instance.titulo}\n"
                    f"🏢 *Propiedad:* {prop_code}\n"
                    f"🗓 *Fecha:* {instance.fecha_evento}\n"
                    f"⏰ *Horario:* {instance.hora_inicio} a {instance.hora_fin}\n\n"
                    f"📝 *Detalles:*\n{instance.detalle or 'Sin detalles adicionales'}\n\n"
                    f"👉 Ingresa al sistema para *Aceptar* o *Rechazar* este evento."
                )

                threading.Thread(target=_send_chatwoot_whatsapp, args=(agent.phone, custom_message)).start()

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