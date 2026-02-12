from django.db.models.signals import post_save, m2m_changed
from properties.models import RequirementMatch
from notifications.events import on_property_matched
from django.dispatch import receiver
from django.core.cache import cache
import logging
from django.db import transaction
from .models import Property

from .models import Requirement
from . import matching as matching_module

logger = logging.getLogger(__name__)

INACTIVE_AVAILABILITY = {"unavailable", "paused"}

@receiver(post_save, sender=Property)
def sync_is_active_with_availability(sender, instance: Property, **kwargs):
    should_be_active = instance.availability_status not in INACTIVE_AVAILABILITY
    if instance.is_active != should_be_active:
        Property.objects.filter(pk=instance.pk).update(is_active=should_be_active)

@receiver(post_save, sender=Requirement)
def requirement_post_save_recalculate_matches(sender, instance: Requirement, created, **kwargs):
    """Al guardar un Requirement, programar recálculo de coincidencias tras el commit.

    Usamos `transaction.on_commit` para garantizar que los cambios (incluyendo M2M)
    estén persistidos antes de ejecutar el motor de matching. Esto evita casos
    donde `post_save` se ejecuta antes de `form.save_m2m()` y los filtros quedan incompletos.
    """
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

@receiver(post_save, sender=RequirementMatch)
def requirement_match_saved(sender, instance, created, **kwargs):
    # Solo dispara evento, nada más
    on_property_matched(instance)