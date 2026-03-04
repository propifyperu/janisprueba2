# properties/templatetags/requirement_extras.py
from decimal import Decimal
from django import template
from django.utils.formats import number_format

register = template.Library()


def _to_decimal(v):
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _fmt_num(v, decimals=2):
    """
    Respeta locale (coma/punto) usando number_format de Django.
    """
    dv = _to_decimal(v)
    if dv is None:
        return None
    return number_format(dv, decimal_pos=decimals, use_l10n=True, force_grouping=True)


@register.simple_tag
def money_range(symbol, min_val, max_val):
    """
    Reglas:
    - si min=0 y max existe => <= max
    - si min existe y max existe y min != 0 => min - max
    - si min existe y max es None => >= min
    - si solo max existe => <= max
    - si no hay nada => '-'
    """
    dmin = _to_decimal(min_val)
    dmax = _to_decimal(max_val)

    if dmin is None and dmax is None:
        return "-"

    sym = symbol or ""

    # solo max
    if dmin is None and dmax is not None:
        return f"<= {sym} {_fmt_num(dmax)}".strip()

    # solo min
    if dmin is not None and dmax is None:
        # si min = 0 y no hay max => no aporta, lo ocultamos
        if dmin == 0:
            return "-"
        return f">= {sym} {_fmt_num(dmin)}".strip()

    # ambos
    if dmin == 0:
        return f"<= {sym} {_fmt_num(dmax)}".strip()

    return f"{sym} {_fmt_num(dmin)} - {sym} {_fmt_num(dmax)}".strip()


@register.simple_tag
def area_range(min_val, max_val, unit="m²"):
    """
    Reglas:
    - si min existe y max None => >= min m²
    - si min None y max existe => <= max m²
    - si ambos => min - max m²
    - si no hay => '-'
    """
    dmin = _to_decimal(min_val)
    dmax = _to_decimal(max_val)

    if dmin is None and dmax is None:
        return "-"

    if dmin is None and dmax is not None:
        return f"<= {_fmt_num(dmax)} {unit}"

    if dmin is not None and dmax is None:
        return f">= {_fmt_num(dmin)} {unit}"

    return f"{_fmt_num(dmin)} - {_fmt_num(dmax)} {unit}"