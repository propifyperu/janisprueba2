# properties/engine_matching/engine.py
from typing import Dict, Any, List

from django.db.models import QuerySet

from .criteria import normalize_range, proximity_score
from django.db.models import Q
from properties.models import Property, Requirement


# -----------------------------
# 1) SQL: hard filters
# -----------------------------
def build_candidate_qs(req: Requirement) -> QuerySet[Property]:
    qs = (
        Property.objects
        .filter(is_active=True, is_draft=False)
        .select_related(
            "operation_type",
            "property_type",
            "property_subtype",
            "currency",
            "forma_de_pago",
            "district_fk",
        )
    )

    # (A) OperationType mapping por CODE (NO name)
    # Requirement: buy/rent ; Property: sale/rent
    if req.operation_type_id:
        req_code = (req.operation_type.code or "").strip().lower()

        if req_code == "buy":
            qs = qs.filter(operation_type__code="sale")
        elif req_code == "rent":
            qs = qs.filter(operation_type__code="rent")
        else:
            # fallback: mismo code si existiera (por si agregas otros)
            qs = qs.filter(operation_type__code=req_code)

    # (B) Tipo / subtipo
    if req.property_type_id:
        qs = qs.filter(property_type_id=req.property_type_id)

    if req.property_subtype_id:
        qs = qs.filter(
            Q(property_subtype_id=req.property_subtype_id) | Q(property_subtype__isnull=True)
        )

    # (C) Distritos: FK real (ya NO usamos prop.district char)
    district_ids = list(req.districts.values_list("id", flat=True))
    if district_ids:
        qs = qs.filter(district_fk_id__in=district_ids)

    # (D) Moneda
    if req.currency_id:
        qs = qs.filter(currency_id=req.currency_id)

    # (E) Forma de pago (Requirement.payment_method -> Property.forma_de_pago)
    # Regla:
    # - req CASH  -> Property CASH + cont_y_credito
    # - req credit -> Property credit + cont_y_credito
    # - req cont_y_credito -> Property cont_y_credito (solo)
    if req.payment_method_id and req.payment_method:
        req_code = (req.payment_method.code or "").strip().lower()

        # Nota: normalizamos por si tienes CASH en mayúscula en DB
        if req_code == "cash":
            qs = qs.filter(forma_de_pago__code__in=["CASH", "cash", "cont_y_credito"])
        elif req_code == "credit":
            qs = qs.filter(forma_de_pago__code__in=["credit", "cont_y_credito"])
        elif req_code == "cont_y_credito":
            qs = qs.filter(forma_de_pago__code__in=["cont_y_credito"])
        else:
            # fallback: si agregas nuevos métodos
            qs = qs.filter(forma_de_pago__code__iexact=req_code)

    # (F) Estado comercial (si quieres que sea excluyente)
    # Si NO quieres hacerlo hard filter, comenta esto.
    qs = qs.filter(availability_status="available")

    return qs


# -----------------------------
# 2) Python: scoring
# -----------------------------
def calculate_score(req: Requirement, prop: Property) -> Dict[str, Any]:
    active_fields = {}
    scores = {}

    # -------------------------
    # HARD FILTERS como "peso base"
    # -------------------------
    # Nota: como ya filtraste en SQL, si el prop está aquí, ya cumple.
    hard_fields = []

    if req.operation_type_id:
        hard_fields.append("operation_type")
    if req.property_type_id:
        hard_fields.append("property_type")
    if req.property_subtype_id:
        hard_fields.append("property_subtype")  # ojo: tu SQL deja pasar NULL también
    if req.districts.exists():
        hard_fields.append("districts")
    if req.currency_id:
        hard_fields.append("currency")
    if req.payment_method_id:
        hard_fields.append("payment_method")

    # availability_status siempre lo filtras, pero solo mételo si quieres que pese
    hard_fields.append("availability_status")

    for f in hard_fields:
        active_fields[f] = True
        scores[f] = 1.0

    # -------------------------
    # SOFT SCORE (lo tuyo actual)
    # -------------------------
    pr = normalize_range(req.price_min, req.price_max)
    if pr:
        active_fields["price"] = True
        scores["price"] = proximity_score(prop.price, pr[0], pr[1])

    br = normalize_range(req.bedrooms_min, req.bedrooms_max)
    if br:
        active_fields["bedrooms"] = True
        scores["bedrooms"] = proximity_score(prop.bedrooms, br[0], br[1])

    bar = normalize_range(req.bathrooms_min, req.bathrooms_max)
    if bar:
        active_fields["bathrooms"] = True
        scores["bathrooms"] = proximity_score(prop.bathrooms, bar[0], bar[1])

    gr = normalize_range(req.garage_spaces_min, req.garage_spaces_max)
    if gr:
        active_fields["garage_spaces"] = True
        scores["garage_spaces"] = proximity_score(prop.garage_spaces, gr[0], gr[1])

    lar = normalize_range(req.land_area_min, req.land_area_max)
    if lar:
        active_fields["land_area"] = True
        scores["land_area"] = proximity_score(prop.land_area, lar[0], lar[1])

    bur = normalize_range(req.built_area_min, req.built_area_max)
    if bur:
        active_fields["built_area"] = True
        scores["built_area"] = proximity_score(prop.built_area, bur[0], bur[1])

    fr = normalize_range(req.floors_min, req.floors_max)
    if fr:
        active_fields["floors"] = True
        scores["floors"] = proximity_score(prop.floors, fr[0], fr[1])

    ar = normalize_range(req.antiquity_years_min, req.antiquity_years_max)
    if ar:
        active_fields["antiquity_years"] = True
        scores["antiquity_years"] = proximity_score(prop.antiquity_years, ar[0], ar[1])

    if req.has_elevator is not None:
        active_fields["has_elevator"] = True
        scores["has_elevator"] = 1.0 if req.has_elevator == prop.has_elevator else 0.1

    # ✅ nunca 0 porque al menos metimos hard_fields
    weight = 100.0 / len(active_fields)

    total = 0.0
    details = {}
    for field, sub in scores.items():
        contribution = sub * weight
        total += contribution
        details[field] = {
            "subscore": round(sub, 3),
            "weight": round(weight, 2),
            "contribution": round(contribution, 2),
        }

    return {"score": round(total, 2), "details": details}


# -----------------------------
# 3) Entry point
# -----------------------------
def get_matches(req: Requirement, limit: int = 20) -> List[Dict[str, Any]]:
    qs = build_candidate_qs(req)

    results = []
    for prop in qs.iterator():  # iterator() para no reventar RAM si igual vienen muchos
        sc = calculate_score(req, prop)
        results.append({"property": prop, "score": sc["score"], "details": sc["details"]})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]