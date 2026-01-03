def user_profile(request):
    """Context processor que expone `profile` en todas las plantillas.

    Si el usuario está autenticado intenta obtener `request.user.profile`.
    Si no existe, lo crea con valores por defecto. Devuelve `{'profile': profile}`.
    """
    profile = None
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            profile = user.profile
        except Exception:
            try:
                # Importar localmente para evitar import-time side effects
                from .models import UserProfile
                profile = UserProfile.objects.create(user=user)
            except Exception:
                profile = None

    return {'profile': profile}
