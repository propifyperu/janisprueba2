from django import template

register = template.Library()


@register.filter
def can_view_field(field_permissions_dict, field_name):
    """
    Verifica si un campo debe ser visible basándose en el diccionario de permisos.
    Uso en template: {% if field_permissions|can_view_field:"price" %}...{% endif %}
    """
    if not field_permissions_dict:
        return True  # Por defecto, si no hay restricciones, es visible
    
    if field_name in field_permissions_dict:
        return field_permissions_dict[field_name].get('can_view', True)
    
    return True  # Si no hay restricción específica, es visible


@register.filter
def can_edit_field(field_permissions_dict, field_name):
    """
    Verifica si un campo puede ser editado basándose en el diccionario de permisos.
    Uso en template: {% if field_permissions|can_edit_field:"price" %}...{% endif %}
    """
    if not field_permissions_dict:
        return False  # Por defecto, no puede editar
    
    if field_name in field_permissions_dict:
        return field_permissions_dict[field_name].get('can_edit', False)
    
    return False  # Si no hay permiso explícito, no puede editar


@register.filter
def get_field_permission(field_permissions_dict, field_name):
    """
    Obtiene el diccionario de permisos para un campo específico.
    Uso en template: {% with perm=field_permissions|get_field_permission:"price" %}
    """
    if not field_permissions_dict:
        return {'can_view': True, 'can_edit': False}
    
    if field_name in field_permissions_dict:
        return field_permissions_dict[field_name]
    
    return {'can_view': True, 'can_edit': False}
