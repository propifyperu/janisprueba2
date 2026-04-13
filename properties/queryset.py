from django.db.models import Q
from users.roles import is_privileged


def _apply_role_visibility_filter(user, qs):
    """
    Regla:
    - Si la propiedad NO tiene roles configurados => visible normalmente
    - Si SÍ tiene roles configurados => solo visible si el rol del usuario está incluido
    """
    user_role_id = getattr(user, "role_id", None)

    if not user_role_id:
        return qs.filter(visible_for_roles__isnull=True)

    return qs.filter(
        Q(visible_for_roles__isnull=True) |
        Q(visible_for_roles__id=user_role_id)
    ).distinct()


def visible_properties_for(user, qs):
    """
    qs: queryset base
    """
    if is_privileged(user):
        return qs

    qs = qs.filter(
        Q(is_active=True, is_draft=False) |
        Q(is_draft=True, responsible=user)
    )

    return _apply_role_visibility_filter(user, qs)


def my_properties_for(user, qs):
    return qs.filter(responsible=user, is_active=True).filter(Q(is_draft=False))


def can_user_see_property(user, property_obj):
    """
    Validación para detalle / pdf / timeline.
    """
    if is_privileged(user):
        return True

    base_visible = (
        (property_obj.is_active and not property_obj.is_draft) or
        (property_obj.is_draft and property_obj.responsible_id == user.id)
    )

    if not base_visible:
        return False

    role_ids = list(property_obj.visible_for_roles.values_list("id", flat=True))
    if not role_ids:
        return True

    return getattr(user, "role_id", None) in role_ids