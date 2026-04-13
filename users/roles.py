# users/roles.py

from typing import Optional

# --- code_name EXACTOS (según tu admin/screenshot) ---
ROLE_BACK_OFFICE = "back_office"
ROLE_ABOGADO = "abogado"
ROLE_MANAGER = "manager"
ROLE_DEVELOPER = "developer"
ROLE_MARKETING_DIRECTOR = "marketing_director"
ROLE_PORTFOLIO_DIRECTOR = "portfolio_director"
ROLE_DIRECTORA_COMERCIAL = "directora_comercial"
ROLE_AGENTE_EXTERNO = "agente_e"
ROLE_AGENTE_INTERNO = "agente_i"
ROLE_CALL_CENTER = "call_center"


PRIVILEGED_ROLES = {
    ROLE_MANAGER,
    ROLE_DEVELOPER,
    ROLE_BACK_OFFICE,
    ROLE_MARKETING_DIRECTOR,
    ROLE_CALL_CENTER,
}

AGENT_ROLES = {
    ROLE_AGENTE_INTERNO,
    ROLE_AGENTE_EXTERNO,
}


def get_role_code(user) -> Optional[str]:
    role = getattr(user, "role", None)
    code = getattr(role, "code_name", None) if role else None
    return code.strip().lower() if isinstance(code, str) else None


def is_privileged(user) -> bool:
    # superuser siempre es privilegiado, aunque role esté mal seteado
    if getattr(user, "is_superuser", False):
        return True
    return get_role_code(user) in PRIVILEGED_ROLES


def is_agent(user) -> bool:
    return get_role_code(user) in AGENT_ROLES