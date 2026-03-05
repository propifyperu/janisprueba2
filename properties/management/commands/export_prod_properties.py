import json
from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict

from properties.models import Property, PropertyImage

try:
    # Si tu PropertyDocument está en properties.models
    from properties.models import PropertyDocument
except Exception:
    PropertyDocument = None


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    return str(obj)


class Command(BaseCommand):
    help = "Exporta properties desde la BD actual (ideal: PROD) a un JSON para importar luego en STAGING."

    def add_arguments(self, parser):
        parser.add_argument("--out", required=True, help="Ruta del JSON de salida, ej: docs/exports/prod_props.json")
        parser.add_argument("--last", type=int, default=0, help="Exporta las últimas N properties (por created_at)")
        parser.add_argument("--all", action="store_true", help="Exporta todas las properties")
        parser.add_argument("--codes", nargs="*", help="Lista de codes específicos a exportar")

    def handle(self, *args, **opts):
        out_path = opts["out"]
        last_n = int(opts["last"] or 0)
        export_all = bool(opts["all"])
        codes = opts.get("codes") or []

        # Validación de modos
        modes = sum([1 if last_n > 0 else 0, 1 if export_all else 0, 1 if len(codes) > 0 else 0])
        if modes != 1:
            raise SystemExit("Usa EXACTAMENTE uno: --last N  ó  --all  ó  --codes ...")

        qs = Property.objects.all()

        if codes:
            qs = qs.filter(code__in=codes)
        elif last_n > 0:
            qs = qs.order_by("-created_at")[:last_n]
        else:
            qs = qs.order_by("id")

        # Campos “seguros” (no exportamos IDs internos de FKs; exportamos por 'code' o 'name')
        export_items = []
        total = qs.count() if not last_n else len(qs)

        self.stdout.write(self.style.WARNING(f"Exportando {total} properties..."))

        for i, p in enumerate(qs, start=1):
            # Property base
            item = {
                "code": p.code,
                "title": p.title,
                "description": p.description,
                "price": str(p.price) if p.price is not None else None,
                "availability_status": p.availability_status,
                "department": p.department,
                "province": p.province,
                "district": p.district,
                "urbanization": p.urbanization,
                "coordinates": p.coordinates,
                "exact_address": p.exact_address,
                "real_address": p.real_address,
                "land_area": str(p.land_area) if p.land_area is not None else None,
                "built_area": str(p.built_area) if p.built_area is not None else None,
                "floors": p.floors,
                "bedrooms": p.bedrooms,
                "bathrooms": p.bathrooms,
                "half_bathrooms": p.half_bathrooms,
                "garage_spaces": p.garage_spaces,
                "antiquity_years": p.antiquity_years,
                "delivery_date": p.delivery_date.isoformat() if p.delivery_date else None,

                # source tracking
                "source": p.source,
                "source_url": p.source_url,
                "source_published_at": p.source_published_at.isoformat() if getattr(p, "source_published_at", None) else None,

                # FKs por “nombre/código”
                "currency_code": p.currency.code if p.currency else None,
                "property_type_name": p.property_type.name if p.property_type else None,
                "property_subtype_name": p.property_subtype.name if p.property_subtype else None,
                "water_service_name": p.water_service.name if p.water_service else None,
                "energy_service_name": p.energy_service.name if p.energy_service else None,
                "drainage_service_name": p.drainage_service.name if p.drainage_service else None,
                "gas_service_name": p.gas_service.name if p.gas_service else None,

                # Responsible user snapshot (solo por email para recreate)
                "responsible": None,
            }

            if p.responsible:
                item["responsible"] = {
                    "email": (p.responsible.email or "").strip() or None,
                    "first_name": p.responsible.first_name or "",
                    "last_name": p.responsible.last_name or "",
                    "phone": getattr(p.responsible, "phone", "") or "",
                }

            # IMÁGENES: NO descargamos nada. Exportamos referencias.
            imgs = []
            for img in PropertyImage.objects.filter(property=p).order_by("order", "id"):
                imgs.append({
                    "image_name": getattr(img.image, "name", "") or "",  # path en storage (clave)
                    "wp_source_url": img.wp_source_url,
                    "order": img.order,
                    "is_primary": img.is_primary,
                    "caption": img.caption or "",
                })
            item["images"] = imgs

            # DOCUMENTOS: exportamos URL para luego descargarlos en staging
            docs = []
            if PropertyDocument is not None:
                for d in p.documents.select_related("document_type").all():
                    dt = getattr(d, "document_type", None)
                    dt_code = getattr(dt, "code", None) if dt else None
                    dt_name = getattr(dt, "name", None) if dt else None

                    file_url = None
                    if getattr(d, "file", None):
                        try:
                            file_url = d.file.url
                        except Exception:
                            file_url = str(d.file)

                    docs.append({
                        "document_type_code": dt_code,
                        "document_type_name": dt_name,
                        "file_url": file_url,
                        "valid_from": d.valid_from.isoformat() if getattr(d, "valid_from", None) else None,
                        "valid_to": d.valid_to.isoformat() if getattr(d, "valid_to", None) else None,
                        "status": getattr(d, "status", None),
                        "notes": getattr(d, "notes", None),
                    })
            item["documents"] = docs

            export_items.append(item)

            if i % 25 == 0:
                self.stdout.write(f"… {i}/{total}")

        payload = {
            "meta": {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "count": len(export_items),
            },
            "items": export_items,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=_json_default)

        self.stdout.write(self.style.SUCCESS(f"OK export -> {out_path} (count={len(export_items)})"))
        