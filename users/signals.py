# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea el UserProfile automáticamente cuando se crea un usuario.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Asegura que si el perfil existe, se guarde cuando el usuario se guarda.
    (No es estrictamente necesario, pero es común.)
    """
    try:
        if hasattr(instance, "profile"):
            instance.profile.save()
    except Exception:
        # Si aún no existe, lo creamos por seguridad
        UserProfile.objects.get_or_create(user=instance)