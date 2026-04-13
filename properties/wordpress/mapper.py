# properties/wordpress/mapper.py
from decimal import Decimal

def _str_or_empty(v):
    return "" if v is None else str(v)

def _as_int(v, default=0):
    try:
        return int(v or default)
    except Exception:
        return default

def property_to_wp_payload(
    p,
    *,
    taxonomy_ids: dict[str, list[int]] | None = None,
    featured_media_id: int | None = None,
    gallery_media_ids: list[int] | None = None,
) -> dict:
    taxonomy_ids = taxonomy_ids or {}
    gallery_media_ids = gallery_media_ids or []

    currency_code = ""
    if getattr(p, "currency", None):
        currency_code = getattr(p.currency, "code", "") or getattr(p.currency, "name", "") or ""

    price = p.price or Decimal("0")
    price_str = f"{price:,.0f}"

    built = _str_or_empty(p.built_area)
    land = _str_or_empty(p.land_area)

    bedrooms = _as_int(p.bedrooms, 0)
    bathrooms = _as_int(p.bathrooms, 0)
    garages = _as_int(p.garage_spaces, 0)
    floors = _as_int(p.floors, 1)

    address = p.exact_address or p.real_address or ""

    lat = ""
    lng = ""
    if p.coordinates and "," in p.coordinates:
        parts = [x.strip() for x in p.coordinates.split(",")]
        if len(parts) >= 2:
            lat, lng = parts[0], parts[1]

    internal_code = (p.codigo_unico_propiedad or p.code or "").strip()
    internal_slug = f"propify-{p.id}"
    
    payload = {
        "title": p.title or "",
        "content": p.description or "",
        "status": "publish" if (p.is_active and not p.is_draft) else "draft",
        "slug": internal_slug,
    }

    # taxonomies (property_type, property_status, etc)
    for k, v in taxonomy_ids.items():
        if v:
            payload[k] = v

    # featured image
    if featured_media_id:
        payload["featured_media"] = featured_media_id

    # ✅ CLAVE: usar "meta" (no property_meta)
    payload["meta"] = {}

    payload["meta"]["fave_property_price"] = [price_str]
    payload["meta"]["fave_property_price_postfix"] = [""]
    payload["meta"]["fave_property_price_prefix"] = [""]
    payload["meta"]["fave_currency"] = [currency_code or "USD"]

    payload["meta"]["fave_property_size"] = [built]
    payload["meta"]["fave_property_size_prefix"] = ["m²"]

    payload["meta"]["fave_property_land"] = [land]
    payload["meta"]["fave_property_land_postfix"] = ["m²"]

    payload["meta"]["fave_property_bedrooms"] = [str(bedrooms)]
    payload["meta"]["fave_property_bathrooms"] = [str(bathrooms)]
    payload["meta"]["fave_property_garage"] = [str(garages)] if garages else [""]

    payload["meta"]["property_floors"] = [str(floors)]

    payload["meta"]["fave_property_map_address"] = [address]
    payload["meta"]["fave_property_address"] = [address]

    payload["meta"]["houzez_geolocation_lat"] = [lat or ""]
    payload["meta"]["houzez_geolocation_long"] = [lng or ""]
    payload["meta"]["fave_property_location"] = [f"{lat},{lng}" if lat and lng else ""]
    payload["meta"]["fave_property_map"] = ["1" if lat and lng else "0"]

    payload["meta"]["fave_property_id"] = [internal_code or ""]
    payload["meta"]["fave_property_rooms"] = [str(bedrooms) if bedrooms else ""]
    payload["meta"]["fave_property_zip"] = [""]
    payload["meta"]["fave_property_year"] = [str(p.antiquity_years or "")]
    payload["meta"]["fave_video_url"] = [""]

    # ✅ galería: lista plana (strings)
    if gallery_media_ids:
        payload["meta"]["fave_property_images"] = [str(x) for x in gallery_media_ids]

    return payload