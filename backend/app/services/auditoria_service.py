from datetime import date, datetime
from typing import Any

from app.api.deps import CurrentUser
from app.controller.cu05_auditoria_logs_controller import CU05AuditoriaLogsController
from app.core.errors import api_error
from app.db import admin_connection, tenant_connection


async def listar_logs(
    *,
    current: CurrentUser,
    empresa_id: str | None = None,
    usuario_id: str | None = None,
    accion: str | None = None,
    entidad: str | None = None,
    fecha_inicio: date | datetime | None = None,
    fecha_fin: date | datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    if current.rol == "superadmin" and current.empresa_id is None:
        async with admin_connection() as conn:
            return await CU05AuditoriaLogsController.listar_logs_conn(
                conn,
                empresa_id=empresa_id,
                include_affected=True,
                usuario_id=usuario_id,
                accion=accion,
                entidad=entidad,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                page=page,
                page_size=page_size,
            )

    if current.empresa_id is None:
        raise api_error(403, "NO_AUTORIZADO", "Se requiere contexto de empresa o superadministrador")

    if empresa_id and str(empresa_id).strip() != str(current.empresa_id):
        raise api_error(
            403,
            "ACCESO_DENEGADO",
            "No puede consultar registros de auditoria de otra empresa",
        )

    async with tenant_connection(current.empresa_id, current.user_id) as conn:
        return await CU05AuditoriaLogsController.listar_logs_conn(
            conn,
            empresa_id=current.empresa_id,
            include_affected=False,
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            page_size=page_size,
        )

