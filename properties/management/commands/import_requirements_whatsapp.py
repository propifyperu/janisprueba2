# properties/management/commands/import_requirements_whatsapp.py
import csv
import json
import re
import hashlib
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from properties.models import Requirement, PropertyOwner, District, OperationType, PropertyStatus


# =========================
# Helpers: encoding + limpieza
# =========================

def open_csv_smart(path: str):
    """
    Abre CSV detectando encoding de verdad (leyendo bytes).
    - Prueba utf-8-sig
    - Luego cp1252 (Excel/Windows típico)
    - Luego latin-1 (último recurso)
    Devuelve un file-like en texto listo para csv.DictReader.
    """
    with open(path, "rb") as bf:
        sample = bf.read(4096)

    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            sample.decode(enc)  # fuerza prueba real
            # errors="replace" evita que vuelva a romper por algún byte raro suelto
            return open(path, "r", encoding=enc, errors="replace", newline="")
        except UnicodeDecodeError:
            continue

    # jamás debería llegar acá, pero por seguridad:
    return open(path, "r", encoding="latin-1", errors="replace", newline="")


def clean_nbsp(s: str) -> str:
    # Limpia el non-breaking space que suele venir del CSV (0xA0 / \u00A0)
    return (s or "").replace("\u00A0", " ").strip()


def norm_name(s: str) -> str:
    s = clean_nbsp(s)
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def parse_date_ddmmyy(s: str):
    s = clean_nbsp(s)
    if not s:
        return None
    return datetime.strptime(s, "%d/%m/%y").date()


def parse_json_relaxed(raw: str):
    if raw is None:
        return None

    s = clean_nbsp(str(raw))
    if not s:
        return None

    # quitar doble llaves típicas "{{...}}"
    if s.startswith("{{") and s.endswith("}}"):
        s = s[1:-1].strip()

    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # fallback controlado: comillas simples -> dobles
        s2 = s.replace("'", '"')
        return json.loads(s2)


def to_decimal(v):
    if v in (None, ""):
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None


def apply_budget_mapping(payload: dict, out: dict):
    bmin = to_decimal(payload.get("budget_min"))
    bmax = to_decimal(payload.get("budget_max"))
    bapp = to_decimal(payload.get("budget_approx"))

    if bmin is not None and bmax is not None:
        out["price_min"] = bmin
        out["price_max"] = bmax
        return
    if bmax is not None:
        out["price_min"] = Decimal("0")
        out["price_max"] = bmax
        return
    if bmin is not None:
        # regla tuya: si solo viene min, lo tratamos como max
        out["price_min"] = Decimal("0")
        out["price_max"] = bmin
        return
    if bapp is not None:
        out["price_min"] = Decimal("0")
        out["price_max"] = bapp
        return


def apply_single_to_range(payload: dict, out: dict, in_key: str, out_min: str, out_max: str):
    v = payload.get(in_key)
    if v in (None, ""):
        return
    dv = to_decimal(v)
    if dv is None:
        return
    out[out_min] = Decimal("0")
    out[out_max] = dv


def parse_district_ids(payload: dict):
    """
    Acepta:
      district: 18
      districts: [38, 27]
      districts: "10,11,13"
    """
    ids = []

    d_single = payload.get("district")
    if d_single not in (None, ""):
        try:
            ids.append(int(d_single))
        except Exception:
            pass

    d_multi = payload.get("districts")
    if d_multi not in (None, ""):
        if isinstance(d_multi, list):
            for x in d_multi:
                try:
                    ids.append(int(x))
                except Exception:
                    pass
        elif isinstance(d_multi, str):
            parts = [p.strip() for p in d_multi.split(",") if p.strip()]
            for p in parts:
                try:
                    ids.append(int(p))
                except Exception:
                    pass

    # unique preserving order
    seen = set()
    out = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_import_batch(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_row_sig(group: str, fecha, contact_name: str, message: str, raw_json_final: str) -> str:
    """
    Firma estable por fila para que el import sea idempotente:
    (import_batch + import_row_sig) => update_or_create
    """
    base = "|".join([
        clean_nbsp(group or ""),
        str(fecha or ""),
        clean_nbsp(contact_name or ""),
        clean_nbsp(message or ""),
        clean_nbsp(raw_json_final or ""),
    ])
    return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()


class Command(BaseCommand):
    help = "Importa requirements desde CSV WhatsApp (JSON ConvertidoFINAL) y los adapta al modelo actual."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Ruta al CSV (ej: docs/RequerimientodeCompra.csv)")

        # 🔥 ahora sí OBLIGATORIO, porque lo usamos para created_by del Requirement y del PropertyOwner
        parser.add_argument("--user-id", type=int, required=True, help="ID del user que quedará como created_by")

        parser.add_argument("--dry-run", action="store_true", help="No guarda en BD, solo valida y muestra resumen")
        parser.add_argument("--limit", type=int, default=0, help="Procesa solo N filas (0 = todas)")

        parser.add_argument(
            "--delete-import",
            action="store_true",
            help="Borra todos los requirements importados desde este CSV (por import_batch)",
        )

        # ✅ Logging sin spam
        parser.add_argument("--verbose", action="store_true", help="Muestra logs resumidos (CREATED/UPDATED), no preview gigante")
        parser.add_argument("--progress-every", type=int, default=200, help="Imprime progreso cada N filas (default 200)")
        parser.add_argument("--preview", action="store_true", help="Imprime preview SOLO para las primeras filas (resumido)")
        parser.add_argument("--preview-limit", type=int, default=10, help="Cuántas filas previsualizar (default 10)")

        # OperationType compra (FORZADO)
        parser.add_argument("--operation-type-code", default="buy", help="Code del OperationType para setear a todos (default: buy)")
        parser.add_argument("--operation-type-name", default="Compra", help="Name fallback si no existe code (default: Compra)")

    def handle(self, *args, **opts):
        path = opts["file"]
        dry_run = bool(opts["dry_run"])
        limit = int(opts["limit"] or 0)
        delete_import = bool(opts["delete_import"])

        verbose = bool(opts.get("verbose"))
        progress_every = int(opts.get("progress_every") or 0)
        preview = bool(opts.get("preview"))
        preview_limit = int(opts.get("preview_limit") or 0)

        import_batch = build_import_batch(path)

        # 1) delete mode
        if delete_import:
            qs = Requirement.objects.filter(import_batch=import_batch)
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f"[DRY] Se borrarían {qs.count()} requirements del batch {import_batch[:10]}..."
                ))
                return

            with transaction.atomic():
                count = qs.count()
                qs.delete()

            self.stdout.write(self.style.SUCCESS(
                f"OK. Borrados {count} requirements del batch {import_batch[:10]}..."
            ))
            return

        # 2) created_by por user-id (OBLIGATORIO)
        User = get_user_model()
        user_id = opts.get("user_id")
        created_by = User.objects.filter(id=user_id).first()
        if not created_by:
            raise CommandError(f"No existe usuario con id={user_id}")

        # 3) OperationType compra obligatorio (FORZADO para todos)
        op = None
        if hasattr(OperationType, "code"):
            op = OperationType.objects.filter(code=opts["operation_type_code"]).first()
        if not op:
            op = OperationType.objects.filter(name__iexact=opts["operation_type_name"]).first()
        if not op:
            raise CommandError(
                f"No existe OperationType para compra. Crea uno con code='{opts['operation_type_code']}' "
                f"o name='{opts['operation_type_name']}'"
            )

        created = 0
        updated = 0
        skipped = 0
        errors = 0

        with open_csv_smart(path) as f:
            # detectar delimiter real (tu archivo suele venir con ';')
            sample = f.read(4096)
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
                reader = csv.DictReader(f, dialect=dialect)
            except Exception:
                reader = csv.DictReader(f, delimiter=";")

            for idx, row in enumerate(reader, start=1):
                if limit and idx > limit:
                    break

                # progreso (sin spam)
                if progress_every and idx % progress_every == 0:
                    self.stdout.write(self.style.WARNING(
                        f"Procesadas {idx} filas... created={created} updated={updated} skipped={skipped} errors={errors}"
                    ))

                try:
                    # Limpieza NBSP en todo lo que es texto
                    group = clean_nbsp(row.get("Grupo WA"))
                    fecha = parse_date_ddmmyy(row.get("Fecha"))
                    contact_name = clean_nbsp(row.get("Nombre_Contacto"))
                    message = clean_nbsp(row.get("Mensaje"))
                    raw_json_final = row.get("JSON ConvertidoFINAL")

                    payload = parse_json_relaxed(raw_json_final) or {}

                    # Firma idempotente por fila
                    row_sig = build_row_sig(group, fecha, contact_name, message, raw_json_final)

                    # 1) Contacto único (simple)
                    contact_obj = None
                    if contact_name:
                        fn = contact_name
                        contact_obj = PropertyOwner.objects.filter(
                            first_name=fn, last_name="", maternal_last_name=""
                        ).first()
                        if not contact_obj and not dry_run:
                            contact_obj = PropertyOwner(
                                first_name=fn,
                                last_name="",
                                maternal_last_name="",
                                created_by=created_by,  # 🔥 evita null created_by_id
                            )
                            contact_obj.save()

                    # 2) Mapear Requirement
                    req_data = {}

                    # SIEMPRE compra
                    req_data["operation_type_id"] = op.id

                    # PropertyStatus desde payload.status -> property_status_id (si existe)
                    st = payload.get("status")
                    if st not in (None, ""):
                        try:
                            st_id = int(st)
                            if PropertyStatus.objects.filter(id=st_id).exists():
                                req_data["property_status_id"] = st_id
                        except Exception:
                            pass

                    # FKs directos (ids)
                    for k in ("property_type", "property_subtype", "currency", "payment_method"):
                        v = payload.get(k)
                        if v not in (None, ""):
                            try:
                                req_data[f"{k}_id"] = int(v)
                            except Exception:
                                pass

                    # ranges directos si ya vinieran
                    for k in (
                        "price_min", "price_max",
                        "bedrooms_min", "bedrooms_max",
                        "bathrooms_min", "bathrooms_max",
                        "garage_spaces_min", "garage_spaces_max",
                        "floors_min", "floors_max",
                        "land_area_min", "land_area_max",
                        "built_area_min", "built_area_max",
                        "antiquity_years_min", "antiquity_years_max",
                    ):
                        if payload.get(k) not in (None, ""):
                            req_data[k] = to_decimal(payload.get(k))

                    # presupuesto viejo -> price_
                    apply_budget_mapping(payload, req_data)

                    # single -> range
                    apply_single_to_range(payload, req_data, "bedrooms", "bedrooms_min", "bedrooms_max")
                    apply_single_to_range(payload, req_data, "bathrooms", "bathrooms_min", "bathrooms_max")
                    apply_single_to_range(payload, req_data, "garage_spaces", "garage_spaces_min", "garage_spaces_max")
                    apply_single_to_range(payload, req_data, "floors", "floors_min", "floors_max")
                    apply_single_to_range(payload, req_data, "land_area_approx", "land_area_min", "land_area_max")

                    # ascensor -> has_elevator
                    asc = payload.get("ascensor")
                    if isinstance(asc, str):
                        asc = asc.strip().lower()
                        if asc == "yes":
                            req_data["has_elevator"] = True
                        elif asc == "no":
                            req_data["has_elevator"] = False

                    # notes refinado (del JSON final)
                    if payload.get("notes"):
                        req_data["notes"] = clean_nbsp(str(payload.get("notes")))

                    # metadata WA
                    req_data["source_group"] = group or None
                    req_data["source_date"] = fecha
                    req_data["notes_message_ws"] = message or None

                    # batch + firma para idempotencia
                    req_data["import_batch"] = import_batch
                    req_data["import_row_sig"] = row_sig  # 🔥 REQUIERE CAMPO en Requirement

                    district_ids = parse_district_ids(payload)

                    # preview resumido SOLO si lo pides y solo primeras N
                    if preview and idx <= preview_limit:
                        self.stdout.write(self.style.NOTICE(
                            f"[{idx}] contact='{contact_name}' group='{group}' date='{fecha}' "
                            f"districts={district_ids} price_max={req_data.get('price_max')} msg='{(message or '')[:80]}'"
                        ))

                    if dry_run:
                        skipped += 1
                        continue

                    # ✅ UPSERT (no duplica)
                    with transaction.atomic():
                        req, was_created = Requirement.objects.update_or_create(
                            import_batch=import_batch,
                            import_row_sig=row_sig,
                            defaults={
                                **req_data,
                                "created_by": created_by,
                                "contact": contact_obj,
                            },
                        )

                        # districts idempotente
                        if district_ids:
                            qs = District.objects.filter(id__in=district_ids)
                            req.districts.set(qs)
                        else:
                            req.districts.clear()

                    if was_created:
                        created += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(
                                f"[{idx}] CREATED contact='{contact_name}' date='{fecha}' group='{group}'"
                            ))
                    else:
                        updated += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(
                                f"[{idx}] UPDATED contact='{contact_name}' date='{fecha}' group='{group}'"
                            ))

                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"Fila {idx} error: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS(
            f"OK. created={created}, updated={updated}, skipped={skipped}, errors={errors}, dry_run={dry_run}, batch={import_batch[:10]}..."
        ))