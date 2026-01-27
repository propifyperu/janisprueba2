from django import template

register = template.Library()

@register.filter
def get_item(d, key):
    try:
        return d.get(key)
    except Exception:
        return None

@register.filter
def index(seq, i):
    try:
        return seq[i]
    except Exception:
        return None

@register.filter
def to_list(start, end):
    try:
        return list(range(start, end))
    except Exception:
        return []

@register.filter
def first(seq):
    try:
        return seq[0]
    except Exception:
        return None
