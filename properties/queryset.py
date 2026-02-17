# properties/querysets.py

from django.db.models import Q
from users.roles import is_privileged


def visible_properties_for(user, qs):
    """
    qs: un queryset base ya armado (con select_related/prefetch si quieres)
    Retorna el queryset filtrado según rol.
    """

    # 2) Regla del bug (is_active NULL/False)
    if is_privileged(user):
        # ve todo (incluye is_active null/false/true, drafts, etc)
        return qs

    # no privilegiado:
    # - ve solo activos
    # - + sus propios borradores (para que no se pierdan)
    return qs.filter(
        Q(is_active=True, is_draft=False) |
        Q(is_draft=True, responsible=user)
    )
    
def my_properties_for(user, qs):
    return qs.filter(responsible=user).filter(Q(is_draft=False) )