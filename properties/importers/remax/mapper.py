from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re
from urllib.parse import urlsplit, urlunsplit

@dataclass
class RemaxRow:
    raw: dict

    def get(self, key: str, default: str = "") -> str:
        v = self.raw.get(key, default)
        if v is None:
            return default
        return str(v).strip()

def _strip_query(url: str) -> str:
    """
    https://...jpg?X-Amz-...  -> https://...jpg
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

def parse_decimal(value: str) -> Decimal | None:
    if not value:
        return None
    try:
        v = value.replace(",", "").replace(" ", "")
        return Decimal(v)
    except (InvalidOperation, ValueError):
        return None

def parse_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None

def parse_date_ddmmyyyy(value: str):
    if not value:
        return None
    value = value.strip()
    # Soporta 27/01/2026 y 6/11/2025
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None

def parse_antiquity_years(value: str) -> int | None:
    """
    '20 Años' -> 20
    '0 Años' -> 0
    vacío -> None
    """
    if not value:
        return None
    m = re.search(r"(\d+)", value)
    return int(m.group(1)) if m else None

def normalize_service(value: str) -> str | None:
    """
    'No Tiene' -> None
    'Municipal' -> 'Municipal'
    """
    if not value:
        return None
    v = value.strip()
    if not v or v.lower() in ("no tiene", "ninguno", "n/a"):
        return None
    return v

def parse_image_urls(value: str) -> list[str]:
    """
    Recibe string con urls separadas por coma.
    Devuelve lista limpia (sin querystring) y solo con extensiones válidas.
    Elimina blank.gif.
    """
    if not value:
        return []
    out = []
    for raw in value.split(","):
        u = raw.strip()
        if not u:
            continue
        if "blank.gif" in u:
            continue
        clean = _strip_query(u)
        low = clean.lower()
        if low.endswith((".jpg", ".jpeg", ".png", ".webp")):
            out.append(clean)
    # quitar duplicados preservando orden
    seen = set()
    final = []
    for u in out:
        if u not in seen:
            seen.add(u)
            final.append(u)
    return final

def map_remax_row(row: dict) -> dict:
    r = RemaxRow(row)

    source = r.get("portal") or "remax"
    code = r.get("ID de la Propiedad")
    if not code:
        raise ValueError("Fila sin 'ID de la Propiedad' (code)")

    # Tus columnas: Tipo (nuevo) y Subtipo
    property_type_name = r.get("Type Property") or r.get("Tipo") or r.get("Tipo de Propiedad")
    property_subtype_name = r.get("Subtipo de Propiedad") or None

    mapped = {
        "source": source,
        "source_url": r.get("URL de la Propiedad") or None,
        "code": code,

        "title": (r.get("Tipo de Propiedad") or "").strip() or (property_type_name or "").strip(),
        "description": r.get("Descripción Detallada") or "",

        "price": parse_decimal(r.get("Precio (USD)")),
        "currency_code": "USD",

        "department": r.get("Departamento") or None,
        "province": r.get("Provincia") or None,
        "district": r.get("Distrito") or None,

        "land_area": parse_decimal(r.get("Área de Terreno (m²)")),
        "built_area": parse_decimal(r.get("Área Construida (m²)")),

        "floors": parse_int(r.get("Número de Pisos")),
        "bedrooms": parse_int(r.get("Número de Habitaciones")),
        "bathrooms": parse_int(r.get("Número de Baños")),
        "garage_spaces": parse_int(r.get("Número de Cocheras")),

        "antiquity_years": parse_antiquity_years(r.get("Antigüedad")),
        "published_date": parse_date_ddmmyyyy(r.get("Fecha de Publicación")),

        "water_service_name": normalize_service(r.get("Servicio de Agua")),
        "energy_service_name": normalize_service(r.get("Energía Eléctrica")),
        "drainage_service_name": normalize_service(r.get("Servicio de Drenaje")),
        "gas_service_name": normalize_service(r.get("Servicio de Gas")),

        "property_type_name": (property_type_name or "").strip() or None,
        "property_subtype_name": (property_subtype_name or "").strip() or None,

        "agent_name": r.get("Agente Inmobiliario") or None,
        "agent_email": r.get("Email del Agente") or None,
        "agent_phone": r.get("Teléfono del Agente") or None,

        "image_urls": parse_image_urls(r.get("Imágenes de la Propiedad")),
    }

    return mapped