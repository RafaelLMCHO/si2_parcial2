from fastapi import Depends

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error


def require_superadmin(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current.empresa_id is not None or current.rol != "superadmin":
        raise api_error(403, "SUPERADMIN_REQUERIDO", "Se requiere rol Superadministrador SaaS")
    return current


def require_tenant_admin(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current.empresa_id is None or current.rol != "administrador":
        raise api_error(403, "ADMINISTRADOR_REQUERIDO", "Se requiere rol Administrador de Empresa")
    return current


def require_admin_or_superadmin(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current.rol == "superadmin" and current.empresa_id is None:
        return current
    if current.rol == "administrador" and current.empresa_id is not None:
        return current
    raise api_error(403, "NO_AUTORIZADO", "Se requiere rol Superadministrador o Administrador de Empresa")
