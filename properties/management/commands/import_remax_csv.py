from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from properties.importers.remax.importer import read_csv_rows, upsert_property
from properties.importers.remax.mapper import map_remax_row


class Command(BaseCommand):
    help = "Importa/actualiza properties desde CSV RE/MAX (delimiter ;, ISO-8859-1)"

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Ruta al CSV")
        parser.add_argument("--user-id", required=True, type=int, help="ID del usuario (created_by / uploaded_by)")
        parser.add_argument("--dry-run", action="store_true", help="No escribe en DB")
        parser.add_argument("--images", action="store_true", help="Descarga y crea PropertyImage")
        parser.add_argument("--limit", type=int, default=0, help="Limitar filas (0 = todas)")

    def handle(self, *args, **opts):
        file_path = opts["file"]
        user_id = opts["user_id"]
        dry_run = opts["dry_run"]
        import_images = opts["images"]
        limit = opts["limit"]

        User = get_user_model()
        user = User.objects.get(id=user_id)

        created = 0
        updated = 0
        errors = 0

        for idx, row in enumerate(read_csv_rows(file_path), start=1):
            if limit and idx > limit:
                break
            try:
                mapped = map_remax_row(row)

                if dry_run:
                    self.stdout.write(f"DRY-RUN ✅ fila={idx} code={mapped.get('code')}")
                    continue

                obj, was_created = upsert_property(mapped, created_by=user, import_images=import_images)

                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ CREATED code={obj.code} id={obj.id}"))
                else:
                    updated += 1
                    self.stdout.write(f"♻️ UPDATED code={obj.code} id={obj.id}")

            except Exception as e:
                errors += 1
                self.stderr.write(f"❌ [Fila {idx}] code={row.get('ID de la Propiedad')} ERROR: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"OK. created={created}, updated={updated}, errors={errors}, dry_run={dry_run}, images={import_images}"
        ))