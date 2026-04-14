import json
import os
from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from properties.models import Property


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    return str(obj)


def _related_min(obj):
    """
    Devuelve solo lo mínimo:
    {
        "id": ...,
        "name": ...
    }
    """
    if obj is None:
        return None

    name = None

    # prioridad para nombres legibles
    if hasattr(obj, "full_name"):
        try:
            name = obj.full_name
        except Exception:
            name = None

    if not name and hasattr(obj, "get_full_name"):
        try:
            name = obj.get_full_name()
        except Exception:
            name = None

    if not name and hasattr(obj, "name"):
        try:
            name = obj.name
        except Exception:
            name = None

    if not name and hasattr(obj, "title"):
        try:
            name = obj.title
        except Exception:
            name = None

    if not name and hasattr(obj, "username"):
        try:
            name = obj.username
        except Exception:
            name = None

    if not name:
        try:
            name = str(obj)
        except Exception:
            name = None

    return {
        "id": getattr(obj, "pk", None),
        "name": name,
    }


def _serialize_m2m_min(instance, field_name):
    try:
        return [_related_min(obj) for obj in getattr(instance, field_name).all()]
    except Exception:
        return []


class Command(BaseCommand):
    help = "Exporta properties con un JSON compacto solo con los campos requeridos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            required=True,
            help="Ruta del JSON de salida, ej: docs/exports/prod_props.json"
        )
        parser.add_argument(
            "--last",
            type=int,
            default=0,
            help="Exporta las últimas N properties (por created_at)"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Exporta todas las properties"
        )
        parser.add_argument(
            "--codes",
            nargs="*",
            help="Lista de codes específicos a exportar"
        )

    def handle(self, *args, **opts):
        out_path = opts["out"]
        last_n = int(opts["last"] or 0)
        export_all = bool(opts["all"])
        codes = opts.get("codes") or []

        modes = sum([
            1 if last_n > 0 else 0,
            1 if export_all else 0,
            1 if len(codes) > 0 else 0
        ])
        if modes != 1:
            raise SystemExit("Usa EXACTAMENTE uno: --last N  ó  --all  ó  --codes ...")

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        qs = (
            Property.objects.all()
            .select_related(
                "owner",
                "property_type",
                "property_subtype",
                "status",
                "condition",
                "operation_type",
                "responsible",
                "currency",
                "forma_de_pago",
                "garage_type",
                "land_area_unit",
                "built_area_unit",
                "district_fk",
                "urbanization_fk",
                "water_service",
                "energy_service",
                "drainage_service",
                "gas_service",
                "created_by",
                "assigned_agent",
            )
            .prefetch_related(
                "tags",
                "visible_for_roles",
            )
        )

        if codes:
            qs = qs.filter(code__in=codes).order_by("id")
        elif last_n > 0:
            qs = qs.order_by("-created_at")[:last_n]
        else:
            qs = qs.order_by("id")

        total = qs.count() if hasattr(qs, "count") else len(qs)
        self.stdout.write(self.style.WARNING(f"Exportando {total} properties..."))

        items = []

        for i, p in enumerate(qs, start=1):
            item = {
                "id": p.id,
                "code": p.code,
                "codigo_unico_propiedad": p.codigo_unico_propiedad,
                "title": p.title,
                "description": p.description,

                "owner": _related_min(p.owner),
                "property_type": _related_min(p.property_type),
                "property_subtype": _related_min(p.property_subtype),

                "availability_status": p.availability_status,
                "status": _related_min(p.status),
                "condition": _related_min(p.condition),
                "operation_type": _related_min(p.operation_type),

                "wp_post_id": p.wp_post_id,
                "wp_slug": p.wp_slug,
                "wp_last_sync": p.wp_last_sync,

                "source": p.source,
                "source_url": p.source_url,
                "source_published_at": p.source_published_at,

                "responsible": _related_min(p.responsible),

                "antiquity_years": p.antiquity_years,
                "delivery_date": p.delivery_date,
                "price": p.price,

                "currency": _related_min(p.currency),
                "forma_de_pago": _related_min(p.forma_de_pago),

                "maintenance_fee": p.maintenance_fee,
                "has_maintenance": p.has_maintenance,

                "floors": p.floors,
                "bedrooms": p.bedrooms,
                "bathrooms": p.bathrooms,
                "half_bathrooms": p.half_bathrooms,

                "garage_spaces": p.garage_spaces,
                "garage_type": _related_min(p.garage_type),
                "parking_cost_included": p.parking_cost_included,
                "parking_cost": p.parking_cost,

                "land_area": p.land_area,
                "land_area_unit": _related_min(p.land_area_unit),
                "built_area": p.built_area,
                "built_area_unit": _related_min(p.built_area_unit),
                "front_measure": p.front_measure,
                "depth_measure": p.depth_measure,

                "real_address": p.real_address,
                "exact_address": p.exact_address,
                "coordinates": p.coordinates,

                "district_fk": _related_min(p.district_fk),
                "urbanization_fk": _related_min(p.urbanization_fk),

                "water_service": _related_min(p.water_service),
                "energy_service": _related_min(p.energy_service),
                "drainage_service": _related_min(p.drainage_service),
                "gas_service": _related_min(p.gas_service),

                "amenities": p.amenities,
                "zoning": p.zoning,

                "tags": _serialize_m2m_min(p, "tags"),

                "created_by": _related_min(p.created_by),
                "assigned_agent": _related_min(p.assigned_agent),

                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "is_active": p.is_active,

                "visible_for_roles": _serialize_m2m_min(p, "visible_for_roles"),

                "is_draft": p.is_draft,
                "is_ready_for_sale": p.is_ready_for_sale,
                "unit_location": p.unit_location,
                "is_project": p.is_project,
                "project_name": p.project_name,
                "ascensor": p.ascensor,
                "has_elevator": p.has_elevator,
            }

            items.append(item)

            if i % 25 == 0:
                self.stdout.write(f"… {i}/{total}")

        payload = {
            "meta": {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "count": len(items),
            },
            "items": items,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=_json_default)

        self.stdout.write(self.style.SUCCESS(f"OK export -> {out_path} (count={len(items)})"))