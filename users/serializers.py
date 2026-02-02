# users/api/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.models import UserProfile  # ajusta el import si tu app se llama distinto

User = get_user_model()


class UserMeProfileSerializer(serializers.ModelSerializer):
    # Campos del perfil "aplanados" usando source="profile.<campo>"
    bio = serializers.CharField(source="profile.bio", required=False, allow_blank=True)
    address = serializers.CharField(source="profile.address", required=False, allow_blank=True)
    date_of_birth = serializers.DateField(source="profile.date_of_birth", required=False, allow_null=True)

    email_notifications = serializers.BooleanField(source="profile.email_notifications", required=False)
    whatsapp_notifications = serializers.BooleanField(source="profile.whatsapp_notifications", required=False)
    push_notifications = serializers.BooleanField(source="profile.push_notifications", required=False)
    theme = serializers.ChoiceField(source="profile.theme", choices=UserProfile.THEME_CHOICES, required=False)

    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            # read-only útiles para UI
            "id",
            "username",
            "avatar_url",

            # editables (CustomUser)
            "first_name",
            "last_name",
            "email",
            "phone",

            # editables (UserProfile)
            "bio",
            "address",
            "date_of_birth",
            "email_notifications",
            "whatsapp_notifications",
            "push_notifications",
            "theme",
        ]
        read_only_fields = ["id", "username", "avatar_url"]

    def get_avatar_url(self, obj):
        # obj.profile viene por related_name='profile'
        try:
            profile = obj.profile
        except Exception:
            return None
        if profile.avatar:
            # devuelve URL del storage (Azure si está configurado)
            return profile.avatar.url
        return None

    def validate_email(self, value: str):
        """
        Email único (case-insensitive), permitiendo el del mismo usuario.
        """
        if not value:
            return value

        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def update(self, instance, validated_data):
        """
        Actualiza User + crea/actualiza UserProfile.
        validated_data puede traer: {"profile": {...}} por los source="profile.xxx"
        """
        profile_data = validated_data.pop("profile", None)

        # 1) Actualizar CustomUser
        user = super().update(instance, validated_data)

        # 2) Actualizar UserProfile (crear si no existe)
        if profile_data is not None:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return user