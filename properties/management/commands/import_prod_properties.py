import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from properties.models import (
    Property,
    PropertyType,
    PropertySubtype,
    Currency,
    WaterServiceType,
    EnergyServiceType,
    DrainageServiceType,
    GasServiceType,
    PropertyImage,
)

try:
    from properties.models import PropertyDocument
except Exception:
    PropertyDocument = None

try:
    # Ajusta este import si tu DocumentType está en otro app (catalogs)
    from catalogs.models import DocumentType
except Exception:
    DocumentType = None


def _to_decimal(v):
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _parse_iso_date(s):
    if not s:
        return None
    try:
        # "YYYY-MM-DD"
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def _get_or_create_property_type(name):
    if not name:
        return None
    obj, _ = PropertyType.objects.get_or_create(name=name)
    return obj


def _get_or_create_property_subtype(pt, name):
    if not pt or not name:
        return None
    obj, _ = PropertySubtype.objects.get_or_create(property_type=pt, name=name)
    return obj


def _get_currency(code_or_id):
    if not code_or_id:
        return None
    s = str(code_or_id).strip()
    if not s:
        return None
    if s.isdigit():
        return Currency.objects.filter(id=int(s)).first()
    return Currency.objects.filter(code__iexact=s).first()


def _get_service(model, name):
    if not name:
        return None
    # Solo buscar para no ensuciar catálogos
    return model.objects.filter(name__iexact=name).first()


def _split_name(fullname: str):
    fullname = (fullname or "").strip()
    if not fullname:
        return "", ""
    parts = fullname.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _make_unique_username(base: str) -> str:
    base = slugify(base) or "user"
    User = get_user_model()
    username = base[:150]
    i = 1
    while User.objects.filter(username=username).exists():
        i += 1
        suffix = f"-{i}"
        username = (base[:150 - len(suffix)] + suffix)
    return username


def _get_or_create_user_by_email(snapshot: dict | None):
    """
    Regla: crear usuario SOLO si no existe por email.
    """
    if not snapshot:
        return None

    email = (snapshot.get("email") or "").strip().lower()
    if not email:
        return None

    User = get_user_model()
    u = User.objects.filter(email__iexact=email).first()
    if u:
        return u

    first_name = snapshot.get("first_name") or ""
    last_name = snapshot.get("last_name") or ""
    phone = snapshot.get("phone") or ""

    base = email.split("@")[0] if email else (first_name + "-" + last_name)
    username = _make_unique_username(base)

    u = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        is_active=True,
        is_verified=False,
        is_active_agent=True,
    )
    return u


def _download_file(url: str, timeout=30) -> tuple[bytes | None, str | None]:
    """
    Descarga bytes desde un URL (storage prod). Si falla, retorna (None, None).
    """
    try:
        r = requests.get(url, timeout=timeout, stream=True)
        r.raise_for_status()
        content = r.content
        ctype = r.headers.get("Content-Type", "") or ""
        return content, ctype
    except Exception:
        return None, None


def _filename_from_url(url: str) -> str:
    try:
        path = urlparse(url).path
        name = os.path.basename(path) or "document.bin"
        return name[:200]
    except Exception:
        return "document.bin"


class Command(BaseCommand):
    help = "Importa a STAGING un JSON exportado desde PROD. Imágenes: NO download (solo referencias). Docs: SÍ download."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Ruta al JSON exportado")
        parser.add_argument("--user-id", required=True, type=int, help="Usuario ejecutor (created_by / uploaded_by)")
        parser.add_argument("--mark-source", default="propify", help="Si lo pasas, pisa Property.source con este valor")
        parser.add_argument("--dry-run", action="store_true", help="No escribe en DB (solo valida)")
        parser.add_argument("--docs", action="store_true", help="Descarga y guarda documentos (recomendado)")
        parser.add_argument("--images", action="store_true", help="Copia referencias de imágenes (NO descarga)")
        parser.add_argument("--limit", type=int, default=0, help="Limita items (0=todos)")

    @transaction.atomic
    def handle(self, *args, **opts):
        file_path = opts["file"]
        user_id = opts["user_id"]
        mark_source = (opts["mark_source"] or "").strip() or None
        dry_run = bool(opts["dry_run"])
        do_docs = bool(opts["docs"])
        do_images = bool(opts["images"])
        limit = int(opts["limit"] or 0)

        User = get_user_model()
        actor = User.objects.get(id=user_id)

        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        items = payload.get("items") or []
        if limit and limit > 0:
            items = items[:limit]

        created = 0
        updated = 0
        errors = 0
        docs_downloaded = 0
        imgs_linked = 0

        self.stdout.write(self.style.WARNING(
            f"Importando {len(items)} properties | images={'ON' if do_images else 'OFF'} | docs={'ON' if do_docs else 'OFF'} | dry_run={dry_run}"
        ))

        for idx, it in enumerate(items, start=1):
            try:
                code = str(it.get("code") or "").strip()
                if not code:
                    raise ValueError("Item sin code")

                if dry_run:
                    continue

                # Responsible: crea solo si no existe por email
                responsible = _get_or_create_user_by_email(it.get("responsible"))

                # Catálogos / FKs
                pt = _get_or_create_property_type(it.get("property_type_name"))
                pst = _get_or_create_property_subtype(pt, it.get("property_subtype_name"))
                currency = _get_currency(it.get("currency_code"))

                water = _get_service(WaterServiceType, it.get("water_service_name"))
                energy = _get_service(EnergyServiceType, it.get("energy_service_name"))
                drainage = _get_service(DrainageServiceType, it.get("drainage_service_name"))
                gas = _get_service(GasServiceType, it.get("gas_service_name"))

                defaults = {
                    "title": it.get("title") or "",
                    "description": it.get("description") or "",

                    "price": _to_decimal(it.get("price")),
                    "currency": currency,

                    "availability_status": it.get("availability_status") or "available",

                    "department": it.get("department"),
                    "province": it.get("province"),
                    "district": it.get("district"),
                    "urbanization": it.get("urbanization"),

                    "coordinates": it.get("coordinates"),
                    "exact_address": it.get("exact_address"),
                    "real_address": it.get("real_address"),

                    "land_area": _to_decimal(it.get("land_area")),
                    "built_area": _to_decimal(it.get("built_area")),

                    "floors": it.get("floors"),
                    "bedrooms": it.get("bedrooms"),
                    "bathrooms": it.get("bathrooms"),
                    "half_bathrooms": it.get("half_bathrooms"),
                    "garage_spaces": it.get("garage_spaces"),

                    "antiquity_years": it.get("antiquity_years"),
                    "delivery_date": _parse_iso_date(it.get("delivery_date")),

                    "property_type": pt,
                    "property_subtype": pst,

                    "water_service": water,
                    "energy_service": energy,
                    "drainage_service": drainage,
                    "gas_service": gas,

                    "responsible": responsible,

                    # source tracking
                    "source": mark_source or "propify",
                    "source_url": it.get("source_url"),
                    "source_published_at": _parse_iso_date(it.get("source_published_at")),

                    "created_by": actor,
                }

                obj, was_created = Property.objects.update_or_create(
                    code=code,
                    defaults=defaults,
                )

                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ [CREATED] code={code} (#{idx})"))
                else:
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(f"♻️  [UPDATED] code={code} (#{idx})"))

                # IMÁGENES: NO download. Solo linkear al storage (image.name) + wp_source_url
                if do_images:
                    images = it.get("images") or []
                    if images:
                        existing_wp_urls = set(
                            PropertyImage.objects.filter(property=obj).values_list("wp_source_url", flat=True)
                        )
                        existing_image_names = set(
                            PropertyImage.objects.filter(property=obj).values_list("image", flat=True)
                        )

                        for im in images:
                            wp_url = im.get("wp_source_url")
                            image_name = (im.get("image_name") or "").strip()

                            # evitar duplicados por wp_source_url o image name
                            if wp_url and wp_url in existing_wp_urls:
                                continue
                            if image_name and image_name in existing_image_names:
                                continue

                            pi = PropertyImage(
                                property=obj,
                                uploaded_by=actor,
                                order=int(im.get("order") or 0),
                                is_primary=bool(im.get("is_primary")),
                                caption=im.get("caption") or "",
                                wp_source_url=wp_url or None,
                            )

                            # CLAVE: NO descargamos. Solo referenciamos el archivo ya existente en storage.
                            # Si image_name viene vacío, igual guardamos el registro (pero ojo: ImageField es requerido).
                            # Recomendado: que prod tenga image.name siempre.
                            if not image_name:
                                # Si tu modelo exige image sí o sí, mejor saltar esta imagen
                                # para no romper integridad.
                                continue

                            pi.image.name = image_name
                            pi.save()
                            imgs_linked += 1

                # DOCUMENTOS: SÍ descargar desde file_url y guardar en staging
                if do_docs and PropertyDocument is not None and DocumentType is not None:
                    docs = it.get("documents") or []
                    for d in docs:
                        file_url = d.get("file_url")
                        if not file_url:
                            continue

                        dt_code = d.get("document_type_code")
                        dt_name = d.get("document_type_name")

                        doc_type = None
                        if dt_code:
                            doc_type = DocumentType.objects.filter(code=dt_code).first()
                        if not doc_type and dt_name:
                            doc_type = DocumentType.objects.filter(name=dt_name).first()

                        if not doc_type:
                            # si no existe el tipo, lo saltamos para no inventar
                            continue

                        content, _ctype = _download_file(file_url)
                        if not content:
                            continue

                        filename = _filename_from_url(file_url)

                        # 1 doc por tipo: upsert property+document_type
                        doc_obj = PropertyDocument.objects.filter(property=obj, document_type=doc_type).first()
                        if not doc_obj:
                            doc_obj = PropertyDocument(property=obj, document_type=doc_type)

                        # metadata opcional
                        doc_obj.valid_from = _parse_iso_date(d.get("valid_from"))
                        doc_obj.valid_to = _parse_iso_date(d.get("valid_to"))
                        doc_obj.status = d.get("status")
                        doc_obj.notes = d.get("notes")

                        doc_obj.file.save(filename, ContentFile(content), save=True)
                        docs_downloaded += 1

            except Exception as e:
                errors += 1
                self.stderr.write(self.style.ERROR(f"❌ [#{idx}] code={it.get('code')} ERROR: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"OK import. created={created}, updated={updated}, errors={errors}, images_linked={imgs_linked}, docs_downloaded={docs_downloaded}"
        ))