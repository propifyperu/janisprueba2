"""Lógica de matching entre `Requirement` y `Property`.

- Fase A: filtro duro (excluyente).
- Fase B: scoring ponderado por pesos configurables (`MatchingWeight`).

Funciones principales:
- hard_filter(requirement, queryset): devuelve queryset filtrado por condiciones obligatorias.
- score_property(requirement, prop, weights): devuelve dict con `score` (0..100) y `details`.
- get_matches_for_requirement(requirement, limit=10): aplica fase A y B y devuelve lista ordenada.
- record_positive_match(requirement, prop): guarda `MatchEvent` y ajusta pesos de forma simple.

Notas de diseño:
- Los pesos se guardan en `MatchingWeight.key` con nombres como: "property_type", "district", "price", "area".
- Para campos numéricos (precio, área) se emplea función de proximidad (cuanto más cerca, mayor puntuación).
- Aprendizaje: simple incremento de contadores por criterio al registrar positive events; en producción usar ML o ajustes más robustos.
"""
from typing import Dict, Any, List, Tuple
from django.db.models import QuerySet
from django.utils import timezone
from django.db import transaction

from .models import Requirement, Property, MatchingWeight, MatchEvent, RequirementMatch



def _load_weights() -> Dict[str, float]:
    weights = {mw.key: mw.weight for mw in MatchingWeight.objects.all()}
    # defaults
    defaults = {
        'property_type': 5.0,
        'property_subtype': 3.0,
        'district': 5.0,
        'currency': 2.0,
        'price': 3.0,
        'payment_method': 2.0,
        'property_status': 2.0,
        'area': 2.0,
        'land_area': 2.0,
        'built_area': 2.0,
        'front_measure': 1.0,
        'depth_measure': 1.0,
        'bedrooms': 1.0,
        'bathrooms': 1.0,
        'half_bathrooms': 0.5,
        'garage_spaces': 0.8,
        'garage_type': 0.5,
        'parking_cost_included': 0.5,
        'parking_cost': 0.5,
        'amenities': 1.0,
        'tags': 1.0,
        'water_service': 0.5,
        'energy_service': 0.5,
        'drainage_service': 0.5,
        'gas_service': 0.5,
        'is_project': 0.5,
        'project_name': 0.5,
        'unit_location': 0.5,
        'ascensor': 0.5,
        'floors': 0.5,
    }
    for k, v in defaults.items():
        weights.setdefault(k, v)
    return weights


def hard_filter(requirement: Requirement, qs: QuerySet) -> QuerySet:
    """Aplicar filtros duros (excluyentes) sobre `qs`.
    
    Solo mantenemos los filtros que son absolutamente críticos.
    """
    if requirement.property_type:
        qs = qs.filter(property_type=requirement.property_type)

    # El presupuesto lo tratamos preferiblemente como scoring, pero si el usuario
    # pusiere un limite infranqueable se podria añadir aqui. Por ahora es scoring.

    return qs


def _proximity_score(value: float, target_min: float, target_max: float) -> float:
    """Devuelve puntuación entre 0..1 según proximidad de `value` al rango [target_min, target_max].

    - Si target_min/target_max son None, se adapta.
    """
    if target_min is None and target_max is None:
        return 1.0
    if target_min is None:
        # solo max
        if value <= target_max:
            return 1.0
        return max(0.0, 1.0 - (value - target_max) / (abs(target_max) + 1))
    if target_max is None:
        if value >= target_min:
            return 1.0
        return max(0.0, 1.0 - (target_min - value) / (abs(target_min) + 1))
    # dentro del rango
    if target_min <= value <= target_max:
        return 1.0
    # fuera: penalizar según distancia relativa
    if value < target_min:
        return max(0.0, 1.0 - (target_min - value) / (abs(target_min) + 1))
    return max(0.0, 1.0 - (value - target_max) / (abs(target_max) + 1))


def score_property(requirement: Requirement, prop: Property, weights: Dict[str, float]) -> Dict[str, Any]:
    """Calcular puntuación (0..100) entre un requirement y una property.

    Retorna: {'score': float, 'details': {criterion: contrib}}
    """
    total_weight = 0.0
    score_acc = 0.0
    details = {}

    # property_type exact match (rigido pero aquí contribuye al score porque hard_filter removes others)
    w = weights.get('property_type', 0)
    total_weight += w
    # consider as matched only if requirement explicitly provided a property_type
    matched = False
    if getattr(requirement, 'property_type', None):
        matched = prop.property_type_id == requirement.property_type_id
    contrib = w if matched else 0.0
    info = 'id_match' if matched else ('no_pref' if not getattr(requirement, 'property_type', None) else 'no_match')
    details['property_type'] = {'contrib': contrib, 'matched': matched, 'info': info}
    score_acc += contrib

    # property_subtype match
    w = weights.get('property_subtype', 0)
    total_weight += w
    matched = False
    if getattr(requirement, 'property_subtype', None):
        matched = prop.property_subtype_id == requirement.property_subtype_id
    contrib = w if matched else 0.0
    info = 'id_match' if matched else ('no_pref' if not getattr(requirement, 'property_subtype', None) else 'no_match')
    details['property_subtype'] = {'contrib': contrib, 'matched': matched, 'info': info}
    score_acc += contrib

    # district exact (compatibilidad con Property que puede tener FK, campo texto, o almacenar id como string)
    w = weights.get('district', 0)
    total_weight += w
    match_district = False
    prop_district_id = getattr(prop, 'district_id', None)
    prop_district_str = getattr(prop, 'district', None)
    if requirement.district_id:
        # preferir comparar por id si la property tiene FK
        if prop_district_id is not None:
            match_district = prop_district_id == requirement.district_id
        elif prop_district_str:
            # si la propiedad guardó un id como string, intentar resolverlo
            try:
                pd = str(prop_district_str).strip()
                if pd.isdigit():
                    try:
                        pd_int = int(pd)
                        match_district = pd_int == requirement.district_id
                    except Exception:
                        match_district = False
                else:
                    # comparar por nombre (normalize)
                    match_district = pd.lower() == str(requirement.district.name).strip().lower()
            except Exception:
                match_district = False
    elif requirement.districts.exists():
        if prop_district_id is not None:
            match_district = prop_district_id in list(requirement.districts.values_list('id', flat=True))
        elif prop_district_str:
            try:
                pd = str(prop_district_str).strip()
                if pd.isdigit():
                    pd_int = int(pd)
                    match_district = pd_int in list(requirement.districts.values_list('id', flat=True))
                else:
                    req_names = [n.strip().lower() for n in requirement.districts.values_list('name', flat=True)]
                    match_district = pd.lower() in req_names
            except Exception:
                match_district = False
    contrib = w if match_district else 0.0
    if not (requirement.district_id or requirement.districts.exists()):
        info = 'no_pref'
    else:
        info = 'id_match' if match_district and prop_district_id is not None else ('name_match' if match_district else 'no_match')
    details['district'] = {'contrib': contrib, 'matched': match_district, 'info': info}
    score_acc += contrib

    # currency
    w = weights.get('currency', 0)
    total_weight += w
    matched = False
    if getattr(requirement, 'currency', None):
        matched = prop.currency_id == requirement.currency_id
    contrib = w if matched else 0.0
    info = 'id_match' if matched else ('no_pref' if not getattr(requirement, 'currency', None) else 'no_match')
    details['currency'] = {'contrib': contrib, 'matched': matched, 'info': info}
    score_acc += contrib

    # payment_method (Forma de pago)
    w = weights.get('payment_method', 0)
    total_weight += w
    matched = False
    if getattr(requirement, 'payment_method', None):
        # En Property es forma_de_pago
        if getattr(prop, 'forma_de_pago', None):
            matched = prop.forma_de_pago_id == requirement.payment_method_id
    contrib = w if matched else 0.0
    info = 'match' if matched else ('no_pref' if not getattr(requirement, 'payment_method', None) else 'no_match')
    details['payment_method'] = {'contrib': contrib, 'matched': matched, 'info': info}
    score_acc += contrib

    # property_status (Condición: Estreno, Antigüedad, etc)
    w = weights.get('property_status', 0)
    total_weight += w
    matched = False
    if getattr(requirement, 'status', None):
        if getattr(prop, 'status', None):
            matched = prop.status_id == requirement.status_id
    contrib = w if matched else 0.0
    info = 'match' if matched else ('no_pref' if not getattr(requirement, 'status', None) else 'no_match')
    details['property_status'] = {'contrib': contrib, 'matched': matched, 'info': info}
    score_acc += contrib

    # price proximity
    w = weights.get('price', 0)
    total_weight += w
    # requirement may be 'approx' or 'range'
    if requirement.budget_type == 'range' and requirement.budget_min is not None and requirement.budget_max is not None:
        prox = _proximity_score(float(prop.price or 0), float(requirement.budget_min), float(requirement.budget_max))
    else:
        target = float(requirement.budget_approx or 0)
        prox = _proximity_score(float(prop.price or 0), target, target)
    contrib = w * prox
    # mark matched only if requirement provided a budget
    price_matched = False
    if requirement.budget_type == 'range':
        price_matched = (requirement.budget_min is not None and requirement.budget_max is not None) and (prox >= 0.99)
    else:
        price_matched = (requirement.budget_approx is not None and requirement.budget_approx != 0) and (prox >= 0.99)
    info = f'proximity:{prox:.3f}' if (requirement.budget_type == 'range' and (requirement.budget_min is not None or requirement.budget_max is not None)) or (requirement.budget_approx is not None) else 'no_pref'
    details['price'] = {'contrib': contrib, 'matched': price_matched, 'info': info}
    score_acc += contrib

    # area proximity (use built_area or land_area depending on requirement.area_type)
    w = weights.get('area', 0)
    total_weight += w
    if requirement.area_type == 'range' and requirement.land_area_min and requirement.land_area_max:
        prox = _proximity_score(float(prop.land_area or 0), float(requirement.land_area_min), float(requirement.land_area_max))
    else:
        target = float(requirement.land_area_approx or 0)
        prox = _proximity_score(float(prop.land_area or 0), target, target)
    contrib = w * prox
    area_matched = False
    if requirement.area_type == 'range':
        area_matched = (requirement.land_area_min is not None and requirement.land_area_max is not None) and (prox >= 0.99)
    else:
        area_matched = (requirement.land_area_approx is not None and requirement.land_area_approx != 0) and (prox >= 0.99)
    info = f'proximity:{prox:.3f}' if (requirement.area_type == 'range' and (requirement.land_area_min is not None or requirement.land_area_max is not None)) or (requirement.land_area_approx is not None) else 'no_pref'
    details['area'] = {'contrib': contrib, 'matched': area_matched, 'info': info}
    score_acc += contrib

    # land_area (explicit key)
    w = weights.get('land_area', 0)
    total_weight += w
    if getattr(requirement, 'land_area_min', None) and getattr(requirement, 'land_area_max', None):
        prox = _proximity_score(float(prop.land_area or 0), float(requirement.land_area_min), float(requirement.land_area_max))
    else:
        prox = 1.0 if not getattr(requirement, 'land_area_approx', None) else _proximity_score(float(prop.land_area or 0), float(getattr(requirement, 'land_area_approx', 0)), float(getattr(requirement, 'land_area_approx', 0)))
    contrib = w * prox
    land_matched = False
    if getattr(requirement, 'land_area_min', None) and getattr(requirement, 'land_area_max', None):
        land_matched = prox >= 0.99
    else:
        land_matched = bool(getattr(requirement, 'land_area_approx', None)) and (prox >= 0.99)
    info = f'proximity:{prox:.3f}' if (getattr(requirement, 'land_area_min', None) or getattr(requirement, 'land_area_approx', None)) else 'no_pref'
    details['land_area'] = {'contrib': contrib, 'matched': land_matched, 'info': info}
    score_acc += contrib

    # built_area
    w = weights.get('built_area', 0)
    total_weight += w
    if getattr(requirement, 'land_area_min', None) and getattr(requirement, 'land_area_max', None):
        # fallback: compare built_area with land_area requirement if applicable
        prox = _proximity_score(float(prop.built_area or 0), float(requirement.land_area_min), float(requirement.land_area_max))
    elif getattr(requirement, 'land_area_approx', None) is not None:
        prox = _proximity_score(float(prop.built_area or 0), float(requirement.land_area_approx), float(requirement.land_area_approx))
    else:
        prox = None
    if prox is None:
        contrib = w * 0.5
        built_matched = False
        info = 'no_pref'
    else:
        contrib = w * prox
        # only mark built_area matched if requirement provided land_area preferences
        built_matched = prox >= 0.99
        info = f'proximity:{prox:.3f}'
    details['built_area'] = {'contrib': contrib, 'matched': built_matched, 'info': info}
    score_acc += contrib

    # bedrooms (simple absolute match penalty)
    w = weights.get('bedrooms', 0)
    total_weight += w
    if requirement.bedrooms is None or requirement.bedrooms == 0:
        contrib = w * 0.5
        matched_bed = False
    else:
        # closer is better
        diff = abs((prop.bedrooms or 0) - requirement.bedrooms)
        prox = max(0.0, 1.0 - diff / (requirement.bedrooms + 1))
        contrib = w * prox
    # mark matched only when requirement provided bedrooms and diff == 0
    if getattr(requirement, 'bedrooms', None) and 'diff' in locals():
        matched_bed = (diff == 0)
    details['bedrooms'] = {'contrib': contrib, 'matched': matched_bed if 'matched_bed' in locals() else False, 'info': (f'diff:{diff}' if getattr(requirement, 'bedrooms', None) else 'no_pref')}
    score_acc += contrib

    # bathrooms
    w = weights.get('bathrooms', 0)
    total_weight += w
    if getattr(requirement, 'bathrooms', None) is None or getattr(requirement, 'bathrooms', 0) == 0:
        contrib = w * 0.5
        bdiff = None
        bmatched = False
    else:
        bdiff = abs((prop.bathrooms or 0) - requirement.bathrooms)
        bprox = max(0.0, 1.0 - bdiff / (requirement.bathrooms + 1))
        contrib = w * bprox
        bmatched = (bdiff == 0)
    details['bathrooms'] = {'contrib': contrib, 'matched': bmatched, 'info': (f'diff:{bdiff}' if getattr(requirement, 'bathrooms', None) else 'no_pref')}
    score_acc += contrib

    # half_bathrooms (medios baños)
    w = weights.get('half_bathrooms', 0)
    total_weight += w
    if getattr(requirement, 'half_bathrooms', None) is None or getattr(requirement, 'half_bathrooms', 0) == 0:
        contrib = w * 0.5
        hbdiff = None
        hbmatched = False
    else:
        hbdiff = abs((prop.half_bathrooms or 0) - requirement.half_bathrooms)
        hbprox = max(0.0, 1.0 - hbdiff / (requirement.half_bathrooms + 1))
        contrib = w * hbprox
        hbmatched = (hbdiff == 0)
    details['half_bathrooms'] = {'contrib': contrib, 'matched': hbmatched, 'info': (f'diff:{hbdiff}' if getattr(requirement, 'half_bathrooms', None) else 'no_pref')}
    score_acc += contrib

    # garage_spaces
    w = weights.get('garage_spaces', 0)
    total_weight += w
    if getattr(requirement, 'garage_spaces', None) is None:
        g_contrib = w * 0.5
        gdiff = None
        gmatched = False
    else:
        gdiff = abs((prop.garage_spaces or 0) - (requirement.garage_spaces or 0))
        gprox = max(0.0, 1.0 - gdiff / ((requirement.garage_spaces or 1) + 1))
        g_contrib = w * gprox
        gmatched = (gdiff == 0)
    details['garage_spaces'] = {'contrib': g_contrib, 'matched': gmatched, 'info': (f'diff:{gdiff}' if getattr(requirement, 'garage_spaces', None) else 'no_pref')}
    score_acc += g_contrib

    # garage_type
    w = weights.get('garage_type', 0)
    total_weight += w
    try:
        req_gt = getattr(requirement, 'garage_type', None)
        prop_gt = getattr(prop, 'garage_type', None)
        matched = False
        contrib = 0.0
        if req_gt and prop_gt:
            try:
                matched = req_gt.id == prop_gt.id
            except Exception:
                matched = str(req_gt).strip().lower() == str(prop_gt).strip().lower()
            contrib = w if matched else 0.0
    except Exception:
        contrib = 0.0
    info = 'match' if contrib > 0 else ('no_pref' if not getattr(requirement, 'garage_type', None) else 'no_match')
    details['garage_type'] = {'contrib': contrib, 'matched': bool(contrib > 0), 'info': info}
    score_acc += contrib

    # parking cost flags
    w = weights.get('parking_cost_included', 0)
    total_weight += w
    try:
        req_flag = getattr(requirement, 'parking_cost_included', None)
        prop_flag = getattr(prop, 'parking_cost_included', None)
        # only consider a match when requirement explicitly set the flag
        matched = False
        if req_flag is not None:
            matched = (req_flag == prop_flag)
        contrib = w if matched else 0.0
    except Exception:
        contrib = 0.0
    info = 'match' if contrib > 0 else ('no_pref' if getattr(requirement, 'parking_cost_included', None) is None else 'no_match')
    details['parking_cost_included'] = {'contrib': contrib, 'matched': bool(contrib > 0), 'info': info}
    score_acc += contrib

    # parking_cost proximity
    w = weights.get('parking_cost', 0)
    total_weight += w
    try:
        if getattr(requirement, 'parking_cost', None) is not None:
            prox = _proximity_score(float(prop.parking_cost or 0), float(requirement.parking_cost), float(requirement.parking_cost))
        else:
            # no preference -> neutral score but not considered a match
            prox = 0.5
    except Exception:
        prox = 1.0
    contrib = w * prox
    park_matched = (getattr(requirement, 'parking_cost', None) is not None) and (prox >= 0.99)
    info = f'proximity:{prox:.3f}' if getattr(requirement, 'parking_cost', None) is not None else 'no_pref'
    details['parking_cost'] = {'contrib': contrib, 'matched': park_matched, 'info': info}
    score_acc += contrib

    # amenities (text) - compare tokens if requirement provides desired amenities
    w = weights.get('amenities', 0)
    total_weight += w
    try:
        prop_amen = (prop.amenities or '').lower()
        req_amen = (getattr(requirement, 'amenities', '') or '').lower()
        if req_amen:
            prop_set = set([t.strip() for t in prop_amen.replace(';',',').split(',') if t.strip()])
            req_set = set([t.strip() for t in req_amen.replace(';',',').split(',') if t.strip()])
            inter = len(prop_set & req_set)
            score_token = inter / max(len(req_set), 1)
        else:
            # no preference: neutral contribution but not a match
            score_token = 0.5
        contrib = w * score_token
    except Exception:
        contrib = 0.0
    am_matched = False
    if req_amen:
        am_matched = contrib > 0
    details['amenities'] = {'contrib': contrib, 'matched': am_matched, 'info': (f'inter:{contrib:.3f}' if req_amen else 'no_pref')}
    score_acc += contrib

    # tags (M2M) - compare if requirement has tags field
    w = weights.get('tags', 0)
    total_weight += w
    try:
        prop_tags = set(prop.tags.values_list('name', flat=True)) if hasattr(prop, 'tags') else set()
        req_tags = set(getattr(requirement, 'tags', []).values_list('name', flat=True)) if hasattr(requirement, 'tags') else set()
        if req_tags:
            inter = len(prop_tags & set([t for t in req_tags]))
            tag_score = inter / max(len(req_tags), 1)
        else:
            tag_score = 0.5
        contrib = w * tag_score
    except Exception:
        contrib = 0.0
    tag_matched = False
    if req_tags:
        tag_matched = contrib > 0
    details['tags'] = {'contrib': contrib, 'matched': tag_matched, 'info': (f'inter:{contrib:.3f}' if req_tags else 'no_pref')}
    score_acc += contrib

    # services (water/energy/drainage/gas) - if requirement provides, compare
    for svc in ('water_service', 'energy_service', 'drainage_service', 'gas_service'):
        w = weights.get(svc, 0)
        total_weight += w
        try:
            req_s = getattr(requirement, svc, None)
            prop_s = getattr(prop, svc, None)
            matched = False
            contrib = 0.0
            if req_s and prop_s:
                try:
                    matched = req_s.id == prop_s.id
                except Exception:
                    matched = str(req_s).strip().lower() == str(prop_s).strip().lower()
                contrib = w if matched else 0.0
        except Exception:
            contrib = 0.0
        info = 'match' if contrib > 0 else ('no_pref' if not getattr(requirement, svc, None) else 'no_match')
        details[svc] = {'contrib': contrib, 'matched': bool(contrib > 0), 'info': info}
        score_acc += contrib

    # project / unit fields
    w = weights.get('is_project', 0)
    total_weight += w
    contrib = w if getattr(requirement, 'is_project', None) == getattr(prop, 'is_project', None) else 0.0
    details['is_project'] = {'contrib': contrib, 'matched': contrib > 0, 'info': ('match' if contrib > 0 else 'no_match')}
    score_acc += contrib

    w = weights.get('unit_location', 0)
    total_weight += w
    try:
        req_ul = getattr(requirement, 'unit_location', None)
        prop_ul = getattr(prop, 'unit_location', None)
        # only consider a positive match when requirement explicitly specifies unit_location
        if req_ul is None:
            contrib = w * 0.5
            ul_matched = False
            ul_info = 'no_pref'
        else:
            ul_matched = (req_ul == prop_ul)
            contrib = w if ul_matched else 0.0
            ul_info = 'match' if ul_matched else 'no_match'
    except Exception:
        contrib = 0.0
        ul_matched = False
        ul_info = 'error'
    details['unit_location'] = {'contrib': contrib, 'matched': ul_matched, 'info': ul_info}
    score_acc += contrib

    w = weights.get('floors', 0)
    total_weight += w
    try:
        if getattr(requirement, 'number_of_floors', None):
            diff = abs((prop.floors or 0) - (requirement.number_of_floors or 0))
            fprox = max(0.0, 1.0 - diff / ((requirement.number_of_floors or 1) + 1))
            contrib = w * fprox
            fmatched = (diff == 0)
            info = f'prox:{fprox:.3f}'
        else:
            contrib = w * 0.5
            fmatched = False
            info = 'no_pref'
    except Exception:
        contrib = 0.0
        fmatched = False
        info = 'error'
    details['floors'] = {'contrib': contrib, 'matched': fmatched, 'info': info}
    score_acc += contrib

    # Normalizar a 0..100
    max_score = total_weight if total_weight > 0 else 1.0
    normalized = (score_acc / max_score) * 100.0
    return {'score': round(normalized, 2), 'details': details}


def get_matches_for_requirement(requirement: Requirement, limit: int = 10) -> List[Dict[str, Any]]:
    """Devuelve lista de propiedades ordenadas por score (aplica fase A y B).

    Cada item: {'property': Property, 'score': float, 'details': {...}}
    """
    weights = _load_weights()
    qs = Property.objects.filter(is_active=True, is_draft=False)
    qs = hard_filter(requirement, qs)

    results: List[Tuple[Property, float, Dict[str, Any]]] = []
    for prop in qs:
        sc = score_property(requirement, prop, weights)
        results.append((prop, sc['score'], sc['details']))

    results.sort(key=lambda x: x[1], reverse=True)
    out = []
    for prop, score, details in results[:limit]:
        out.append({'property': prop, 'score': score, 'details': details})
    return out


@transaction.atomic
def record_positive_match(requirement: Requirement, prop: Property, metadata: Dict[str, Any] | None = None) -> None:
    """Registrar evento positivo y ajustar pesos de forma simple.

    Estrategia simple de aprendizaje:
    - Guardar `MatchEvent`.
    - Incrementar ligeramente los pesos de criterios que coincidieron en este match
      y decrementar levemente los que no coincidieron.
    - Esto es un heurístico; en producción se recomienda usar un algoritmo estadístico/ML.
    """
    MatchEvent.objects.create(requirement=requirement, property=prop, metadata=metadata or {})
    weights = {mw.key: mw for mw in MatchingWeight.objects.all()}

    # criterios a evaluar: property_type, district, price, area, bedrooms
    adjustments = {}
    # property_type
    matched = requirement.property_type_id and prop.property_type_id == requirement.property_type_id
    adjustments['property_type'] = 0.05 if matched else -0.01
    # district
    matched = False
    prop_district_id = getattr(prop, 'district_id', None)
    prop_district_str = getattr(prop, 'district', None)
    if requirement.district_id:
        if prop_district_id is not None:
            matched = prop_district_id == requirement.district_id
        elif prop_district_str:
            try:
                pd = str(prop_district_str).strip()
                if pd.isdigit():
                    matched = int(pd) == requirement.district_id
                else:
                    matched = pd.lower() == str(requirement.district.name).strip().lower()
            except Exception:
                matched = False
    elif requirement.districts.exists():
        if prop_district_id is not None:
            matched = prop_district_id in list(requirement.districts.values_list('id', flat=True))
        elif prop_district_str:
            try:
                pd = str(prop_district_str).strip()
                if pd.isdigit():
                    matched = int(pd) in list(requirement.districts.values_list('id', flat=True))
                else:
                    req_names = [n.strip().lower() for n in requirement.districts.values_list('name', flat=True)]
                    matched = pd.lower() in req_names
            except Exception:
                matched = False
    adjustments['district'] = 0.05 if matched else -0.01
    # price: if within approx/range -> positive
    if requirement.budget_type == 'range' and requirement.budget_min and requirement.budget_max:
        prox = _proximity_score(float(prop.price or 0), float(requirement.budget_min), float(requirement.budget_max))
    else:
        target = float(requirement.budget_approx or 0)
        prox = _proximity_score(float(prop.price or 0), target, target)
    adjustments['price'] = 0.05 * prox - 0.01 * (1 - prox)
    # area
    if requirement.area_type == 'range' and requirement.land_area_min and requirement.land_area_max:
        prox = _proximity_score(float(prop.land_area or 0), float(requirement.land_area_min), float(requirement.land_area_max))
    else:
        target = float(requirement.land_area_approx or 0)
        prox = _proximity_score(float(prop.land_area or 0), target, target)
    adjustments['area'] = 0.03 * prox - 0.005 * (1 - prox)
    # bedrooms
    diff = abs((prop.bedrooms or 0) - (requirement.bedrooms or 0)) if requirement.bedrooms else None
    if diff is None:
        adjustments['bedrooms'] = 0.0
    else:
        adjustments['bedrooms'] = 0.04 if diff == 0 else (-0.01 * min(diff, 5))
    # bathrooms
    if getattr(requirement, 'bathrooms', None) is None:
        adjustments['bathrooms'] = 0.0
    else:
        bdiff = abs((prop.bathrooms or 0) - (requirement.bathrooms or 0))
        adjustments['bathrooms'] = 0.04 if bdiff == 0 else (-0.01 * min(bdiff, 5))
    # half_bathrooms
    if getattr(requirement, 'half_bathrooms', None) is None:
        adjustments['half_bathrooms'] = 0.0
    else:
        hbdiff = abs((prop.half_bathrooms or 0) - (requirement.half_bathrooms or 0))
        adjustments['half_bathrooms'] = 0.03 if hbdiff == 0 else (-0.005 * min(hbdiff, 5))

    # Aplicar ajustes
    for key, delta in adjustments.items():
        mw = weights.get(key)
        if mw:
            mw.weight = max(0.1, mw.weight + delta)
            mw.save()
        else:
            MatchingWeight.objects.create(key=key, weight=max(0.1, 1.0 + delta))

    return None

def persist_matches_for_requirement(requirement: Requirement, limit: int = 50, min_score: float = 0.0):
    """
    Calcula matches (fase A+B) y los guarda en RequirementMatch.
    - actualiza si ya existe
    - opcional: elimina antiguos que ya no están en el top/que bajaron del mínimo
    """
    matches = get_matches_for_requirement(requirement, limit=limit)

    keep_property_ids = []

    for item in matches:
        prop = item['property']
        score = float(item['score'])
        details = item.get('details') or {}

        if score < min_score:
            continue

        keep_property_ids.append(prop.id)

        RequirementMatch.objects.update_or_create(
            requirement=requirement,
            property=prop,
            defaults={
                "score": round(score, 2),
                "details": details,
                "computed_at": timezone.now(),
            }
        )

    # Limpieza opcional: borra matches viejos que ya no están en el top o bajo min_score
    RequirementMatch.objects.filter(requirement=requirement).exclude(property_id__in=keep_property_ids).delete()

    return keep_property_ids