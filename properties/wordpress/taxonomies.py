# properties/wordpress/taxonomies.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional


# ---------------------------------------------------------------------
# 1) Taxonomías "registradas" en WP (solo info de catálogo)
# ---------------------------------------------------------------------

# OJO: para crear properties SOLO te interesan las del CPT "property":
# property_type, property_status, property_feature, property_label,
# property_country, property_state, property_city, property_area
#
# El resto (category, post_tag, nav_menu, wp_pattern_category, agent_*)
# existen en WP pero no son necesarias para crear una property Houzez.

PROPERTY_TAXONOMIES = [
    "property_type",
    "property_status",
    "property_feature",
    "property_label",
    "property_country",
    "property_state",
    "property_city",
    "property_area",
]


# ---------------------------------------------------------------------
# 2) Catálogos (lo que tú ya extrajiste de WP)
#    - Guardamos dos mapas:
#      a) NAME -> ID
#      b) ID -> NAME
#    - Normalizamos en lookup (strip + upper) para evitar errores por mayúsculas
# ---------------------------------------------------------------------

def _key(name: str) -> str:
    return (name or "").strip().upper()


def build_name_to_id(items: Iterable[dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for it in items:
        n = _key(it["name"])
        out[n] = int(it["id"])
    return out


def build_id_to_name(items: Iterable[dict]) -> Dict[int, str]:
    return {int(it["id"]): it["name"] for it in items}


# ----------------------------
# property_type
# ----------------------------
PROPERTY_TYPE_ITEMS = [
    {"id": 5, "name": "Casa"},
    {"id": 6, "name": "Departamento"},
    {"id": 17802, "name": "Duplex"},
    {"id": 7, "name": "Local Comercial"},
    {"id": 17801, "name": "Penthouse"},
    {"id": 17786, "name": "Terreno"},
]
PROPERTY_TYPE_NAME_TO_ID = build_name_to_id(PROPERTY_TYPE_ITEMS)
PROPERTY_TYPE_ID_TO_NAME = build_id_to_name(PROPERTY_TYPE_ITEMS)

# ----------------------------
# property_status
# ----------------------------
PROPERTY_STATUS_ITEMS = [
    {"id": 8, "name": "Alquiler"},
    {"id": 17818, "name": "Antiguedad"},
    {"id": 17821, "name": "Estreno"},
    {"id": 9, "name": "Venta"},
]
PROPERTY_STATUS_NAME_TO_ID = build_name_to_id(PROPERTY_STATUS_ITEMS)
PROPERTY_STATUS_ID_TO_NAME = build_id_to_name(PROPERTY_STATUS_ITEMS)

# ----------------------------
# property_feature (solo los 10 que pasaste; aquí crecerá la lista)
# ----------------------------
PROPERTY_FEATURE_ITEMS = [
    {"id": 11, "name": "Agua Caliente"},
    {"id": 17712, "name": "Aire Acondicionado"},
    {"id": 17788, "name": "Aire acondicionado central"},
    {"id": 17744, "name": "Almacenamiento"},
    {"id": 17789, "name": "Amoblado completo"},
    {"id": 17790, "name": "Área de planchado"},
    {"id": 12, "name": "Ascensor"},
    {"id": 17720, "name": "Aspersores con Medidor"},
    {"id": 17746, "name": "Aspiradora Central"},
    {"id": 17724, "name": "Balcón"},
]
PROPERTY_FEATURE_NAME_TO_ID = build_name_to_id(PROPERTY_FEATURE_ITEMS)
PROPERTY_FEATURE_ID_TO_NAME = build_id_to_name(PROPERTY_FEATURE_ITEMS)

# ----------------------------
# property_label
# ----------------------------
PROPERTY_LABEL_ITEMS = [
    {"id": 17719, "name": "Ideal para Inversión"},
    {"id": 17760, "name": "Listo para Habitar"},
    {"id": 17731, "name": "Nuevo Ingreso"},
    {"id": 17715, "name": "Precio Reducido"},
    {"id": 17742, "name": "Remate"},
    {"id": 17776, "name": "Zona Prime"},
]
PROPERTY_LABEL_NAME_TO_ID = build_name_to_id(PROPERTY_LABEL_ITEMS)
PROPERTY_LABEL_ID_TO_NAME = build_id_to_name(PROPERTY_LABEL_ITEMS)

# ----------------------------
# property_country
# OJO IMPORTANTE: tienes PERU (15237) y Perú (17819).
# Si quieres "una sola fuente", define el CANONICAL_ID acá.
# ----------------------------
PROPERTY_COUNTRY_ITEMS = [
    {"id": 15237, "name": "PERU"},
    {"id": 17819, "name": "Perú"},
]
PROPERTY_COUNTRY_NAME_TO_ID = build_name_to_id(PROPERTY_COUNTRY_ITEMS)
PROPERTY_COUNTRY_ID_TO_NAME = build_id_to_name(PROPERTY_COUNTRY_ITEMS)


# Decide cuál será el "país canonical" que SIEMPRE mandarás.
# Recomendación: usa el que ya tiene más uso/conteo (PERU id=15237).
PROPERTY_COUNTRY_CANONICAL_ID = 15237

PROPERTY_COUNTRY_NAME_TO_ID[_key("PERU")] = PROPERTY_COUNTRY_CANONICAL_ID
PROPERTY_COUNTRY_NAME_TO_ID[_key("Perú")] = PROPERTY_COUNTRY_CANONICAL_ID
PROPERTY_COUNTRY_NAME_TO_ID[_key("Peru")] = PROPERTY_COUNTRY_CANONICAL_ID

# ----------------------------
# property_state
# ----------------------------
PROPERTY_STATE_ITEMS = [
    {"id": 15606, "name": "AREQUIPA"},
]
PROPERTY_STATE_NAME_TO_ID = build_name_to_id(PROPERTY_STATE_ITEMS)
PROPERTY_STATE_ID_TO_NAME = build_id_to_name(PROPERTY_STATE_ITEMS)

# ----------------------------
# property_city
# ----------------------------
PROPERTY_CITY_ITEMS = [
    {"id": 15708, "name": "AREQUIPA"},
    {"id": 17820, "name": "Camana"},
]
PROPERTY_CITY_NAME_TO_ID = build_name_to_id(PROPERTY_CITY_ITEMS)
PROPERTY_CITY_ID_TO_NAME = build_id_to_name(PROPERTY_CITY_ITEMS)

# ----------------------------
# property_area
# ----------------------------
PROPERTY_AREA_ITEMS = [
    {"id": 15709, "name": "ALTO SELVA ALEGRE"},
    {"id": 15793, "name": "AREQUIPA"},
    {"id": 16024, "name": "CAYMA"},
    {"id": 16036, "name": "CERRO COLORADO"},
    {"id": 16076, "name": "CHARACATO"},
    {"id": 16103, "name": "CHIGUATA"},
    {"id": 16541, "name": "JACOBO HUNTER"},
    {"id": 16566, "name": "JOSE LUIS BUSTAMANTE Y RIVERO"},
    {"id": 16601, "name": "LA JOYA"},
    {"id": 16766, "name": "MARIANO MELGAR"},
]
PROPERTY_AREA_NAME_TO_ID = build_name_to_id(PROPERTY_AREA_ITEMS)
PROPERTY_AREA_ID_TO_NAME = build_id_to_name(PROPERTY_AREA_ITEMS)


# ---------------------------------------------------------------------
# 3) Resolver genérico (para usar desde mapper/service)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TaxonomyResolver:
    name_to_id: Dict[str, int]

    def resolve(self, name: Optional[str]) -> Optional[int]:
        if not name:
            return None
        return self.name_to_id.get(_key(name))


RESOLVERS = {
    "property_type": TaxonomyResolver(PROPERTY_TYPE_NAME_TO_ID),
    "property_status": TaxonomyResolver(PROPERTY_STATUS_NAME_TO_ID),
    "property_feature": TaxonomyResolver(PROPERTY_FEATURE_NAME_TO_ID),
    "property_label": TaxonomyResolver(PROPERTY_LABEL_NAME_TO_ID),
    "property_country": TaxonomyResolver(PROPERTY_COUNTRY_NAME_TO_ID),
    "property_state": TaxonomyResolver(PROPERTY_STATE_NAME_TO_ID),
    "property_city": TaxonomyResolver(PROPERTY_CITY_NAME_TO_ID),
    "property_area": TaxonomyResolver(PROPERTY_AREA_NAME_TO_ID),
}


def resolve_term_id(taxonomy: str, name: Optional[str]) -> Optional[int]:
    r = RESOLVERS.get(taxonomy)
    if not r:
        return None
    return r.resolve(name)