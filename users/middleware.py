from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

User = get_user_model()

class HydrateUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        # Si request.user es LazyObject, forzamos evaluación
        user = user._wrapped if hasattr(user, "_wrapped") else user

        # Recargar al usuario con relaciones listas
        request.user = (
            User.objects
            .select_related("role", "department", "profile")
            .only(
                "id", "username", "first_name", "last_name", "is_superuser",
                "role__id", "role__name",
                "department__id", "department__name",
                "profile__id", "profile__theme", "profile__avatar",
            )
            .get(pk=user.pk)
        )