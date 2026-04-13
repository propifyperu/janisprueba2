# users/ui_permissions.py

from users.roles import is_privileged, is_agent


def get_ui_permissions(user) -> dict:
    """
    Flags de UI, sin meter lógica en templates.
    """
    return {
        "is_privileged": is_privileged(user),
        "is_agent": is_agent(user),

        # lo que te causó el bug:
        "can_view_inactive": is_privileged(user),

        # deja placeholders para crecer luego:
        "can_delete_draft": True,  # si quieres luego lo refinamos
    }