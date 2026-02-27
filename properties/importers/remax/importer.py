import csv
import os
import re
from io import BytesIO

import requests
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from users.models import Area, Role
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


def read_csv_rows(file_path: str):
    # CSV: delimiter ; y encoding ISO-8859-1 (como tu archivo)
    with open(file_path, "r", encoding="ISO-8859-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            yield row


def _get_or_create_property_type(name: str | None):
    if not name:
        return None
    obj, _ = PropertyType.objects.get_or_create(name=name)
    return obj


def _get_or_create_property_subtype(pt: PropertyType | None, name: str | None):
    if not pt or not name:
        return None
    obj, _ = PropertySubtype.objects.get_or_create(property_type=pt, name=name)
    return obj


def _get_currency(code: str | None):
    if not code:
        return None
    return Currency.objects.filter(code__iexact=code).first()


def _get_service(model, name: str | None):
    if not name:
        return None
    # puedes decidir si crear o solo buscar. Para no ensuciar, por defecto SOLO busca.
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
    base = slugify(base) or "agent"
    User = get_user_model()
    username = base[:150]
    i = 1
    while User.objects.filter(username=username).exists():
        i += 1
        suffix = f"-{i}"
        username = (base[:150 - len(suffix)] + suffix)
    return username

def _get_default_area_role():
    area = Area.objects.filter(name__iexact="Operaciones").first()
    role = Role.objects.filter(name__iexact="Agente Remax").first()  # o por name
    return area, role


def _get_or_create_agent(name: str | None, email: str | None, phone: str | None):
    User = get_user_model()

    email_norm = (email or "").strip().lower() or None

    # prioridad: por email
    if email_norm:
        u = User.objects.filter(email__iexact=email_norm).first()
        if u:
            # update mínimo
            changed = False
            if phone and not u.phone:
                u.phone = phone
                changed = True
            if not u.is_active_agent:
                u.is_active_agent = True
                changed = True
            if changed:
                u.save(update_fields=["phone", "is_active_agent"])
            return u

    # fallback: crear por nombre
    first_name, last_name = _split_name(name or "")
    base = email_norm.split("@")[0] if email_norm else (first_name + "-" + last_name)
    username = _make_unique_username(base)
    area, role = _get_default_area_role()

    u = User.objects.create(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email_norm or "",
        phone=phone or "",
        is_active_agent=False,
        is_verified=False,
        area=area,
        role=role,
    )
    return u


def _download_image(url: str) -> tuple[bytes, str] | tuple[None, None]:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "") or ""
        return r.content, content_type
    except Exception:
        return None, None


def _filename_from_url(url: str) -> str:
    # simple: ultimo segmento + fallback
    name = url.split("?")[0].rstrip("/").split("/")[-1]
    if not name:
        name = "image.jpg"
    return name[:200]


@transaction.atomic
def upsert_property(mapped: dict, created_by, import_images: bool = False):
    code = str(mapped["code"]).strip()
    if not code:
        raise ValueError("code vacío")

    pt = _get_or_create_property_type(mapped.get("property_type_name"))
    pst = _get_or_create_property_subtype(pt, mapped.get("property_subtype_name"))

    currency = _get_currency(mapped.get("currency_code"))  # USD

    water = _get_service(WaterServiceType, mapped.get("water_service_name"))
    energy = _get_service(EnergyServiceType, mapped.get("energy_service_name"))
    drainage = _get_service(DrainageServiceType, mapped.get("drainage_service_name"))
    gas = _get_service(GasServiceType, mapped.get("gas_service_name"))

    agent = _get_or_create_agent(
        mapped.get("agent_name"),
        mapped.get("agent_email"),
        mapped.get("agent_phone"),
    ) if (mapped.get("agent_name") or mapped.get("agent_email")) else None

    defaults = {
        "source": mapped.get("source") or None,
        "source_url": mapped.get("source_url") or None,
        "source_published_at": mapped.get("published_date"),
        "title": mapped.get("title") or "",
        "description": mapped.get("description") or "",

        "property_type": pt,
        "property_subtype": pst,

        "price": mapped.get("price"),
        "currency": currency,

        "department": mapped.get("department"),
        "province": mapped.get("province"),
        "district": mapped.get("district"),

        "land_area": mapped.get("land_area"),
        "built_area": mapped.get("built_area"),

        "floors": mapped.get("floors"),
        "bedrooms": mapped.get("bedrooms"),
        "bathrooms": mapped.get("bathrooms"),
        "garage_spaces": mapped.get("garage_spaces"),

        "antiquity_years": mapped.get("antiquity_years"),

        "water_service": water,
        "energy_service": energy,
        "drainage_service": drainage,
        "gas_service": gas,

        "responsible": agent,

        "created_by": created_by,
    }

    obj, created = Property.objects.update_or_create(
        code=code,
        defaults=defaults,
    )

    # IMÁGENES (solo si pides --images)
    if import_images:
        urls = mapped.get("image_urls") or []
        if urls:
            # estrategia simple:
            # - si ya tenía imágenes, no duplicar por url
            existing_urls = set(
                PropertyImage.objects.filter(property=obj).values_list("wp_source_url", flat=True)
            )

            for i, url in enumerate(urls):
                if url in existing_urls:
                    continue

                content, content_type = _download_image(url)
                if not content:
                    continue

                filename = _filename_from_url(url)
                pi = PropertyImage(
                    property=obj,
                    uploaded_by=created_by,
                    order=i,
                    is_primary=(i == 0),
                    wp_source_url=url,
                )
                # ImageField es obligatorio -> guardamos archivo real
                pi.image.save(filename, ContentFile(content), save=True)

    return obj, created