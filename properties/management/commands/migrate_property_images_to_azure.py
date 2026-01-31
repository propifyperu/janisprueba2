from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from properties.models import PropertyImage

class Command(BaseCommand):
    help = "Sube a storage (Azure) las PropertyImage que tengan image_blob, y opcionalmente limpia el blob."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No sube nada, solo muestra qué haría.")
        parser.add_argument("--clear-blob", action="store_true", help="Luego de subir, pone image_blob=NULL.")
        parser.add_argument("--only-missing", action="store_true", help="Solo sube si el archivo no existe en storage.")
        parser.add_argument("--limit", type=int, default=0, help="Limita cantidad (0 = sin límite).")

    def handle(self, *args, **opts):
        qs = PropertyImage.objects.exclude(image_blob__isnull=True).exclude(image_blob=b"")
        if opts["limit"]:
            qs = qs.order_by("id")[: opts["limit"]]

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Encontradas {total} imágenes con blob."))

        uploaded = 0
        skipped = 0

        for pi in qs.iterator():
            name = getattr(pi.image, "name", None)
            if not name:
                # Si por alguna razón no hay name, inventamos uno mínimo
                name = f"properties/images/propertyimage_{pi.pk}.jpg"
                pi.image.name = name
                if not opts["dry_run"]:
                    pi.save(update_fields=["image"])

            exists = False
            if opts["only_missing"]:
                try:
                    exists = default_storage.exists(name)
                except Exception:
                    exists = False

            if opts["only_missing"] and exists:
                skipped += 1
                continue

            self.stdout.write(f"[{pi.pk}] subiendo -> {name}")

            if not opts["dry_run"]:
                default_storage.save(name, ContentFile(pi.image_blob))

                if opts["clear_blob"]:
                    PropertyImage.objects.filter(pk=pi.pk).update(image_blob=None, image_content_type=None)

            uploaded += 1

        self.stdout.write(self.style.SUCCESS(
            f"Listo. Subidas: {uploaded}. Saltadas: {skipped}. dry_run={opts['dry_run']} clear_blob={opts['clear_blob']}"
        ))