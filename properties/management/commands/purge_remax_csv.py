from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from properties.models import Property, PropertyImage
from users.models import Role


class Command(BaseCommand):
    help = "Borra todas las propiedades importadas desde RE/MAX (source='remax') y sus agentes (role=Agente Remax)"

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Confirmar borrado")

    def handle(self, *args, **opts):
        if not opts["yes"]:
            self.stdout.write("⚠️ Usa --yes para confirmar.")
            return

        # 1) Properties RE/MAX
        qs = Property.objects.filter(source="remax")
        prop_ids = list(qs.values_list("id", flat=True))

        # 2) Borrar imágenes de esas properties (recomendado)
        img_qs = PropertyImage.objects.filter(property_id__in=prop_ids)
        img_count = img_qs.count()
        img_qs.delete()

        prop_count = qs.count()
        qs.delete()

        # 3) Borrar users con rol "Agente Remax"
        # (por code_name recomendado; fallback por name)
        remax_role = (
            Role.objects.filter(code_name__iexact="agente_remax").first()
            or Role.objects.filter(name__iexact="Agente Remax").first()
        )

        users_deleted = 0
        if remax_role:
            User = get_user_model()
            users_qs = User.objects.filter(role=remax_role)

            # Si quieres NO tocar staff/superusers, deja estas 2 líneas:
            users_qs = users_qs.exclude(is_superuser=True)
            users_qs = users_qs.exclude(is_staff=True)

            users_deleted = users_qs.count()
            users_qs.delete()

        self.stdout.write(self.style.SUCCESS(
            f"OK. deleted_properties={prop_count}, deleted_images={img_count}, deleted_users={users_deleted}"
        ))