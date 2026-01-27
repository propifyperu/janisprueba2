from django.core.cache import cache


def match_notifications(request):
    """Context processor que expone notificaciones de matching para el usuario.

    Lee la clave de cache `user_new_match_alerts_<user_id>` y la devuelve como
    `match_notifications` para ser usada en las plantillas.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'match_notifications': []}

    key = f'user_new_match_alerts_{request.user.id}'
    try:
        data = cache.get(key) or []
    except Exception:
        data = []
    return {'match_notifications': data}
