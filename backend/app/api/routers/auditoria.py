from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser
from app.api.permissions import require_admin_or_superadmin
from app.schemas.auditoria import AuditLogListResponse
from app.services import auditoria_service

router = APIRouter(prefix="/auditoria", tags=["Auditoria y Logs (CU-05)"])


@router.get("/logs", response_model=AuditLogListResponse)
async def listar_auditoria_logs(
    empresa_id: str | None = Query(default=None),
    usuario_id: str | None = Query(default=None),
    accion: str | None = Query(default=None, max_length=30),
    entidad: str | None = Query(default=None, max_length=60),
    fecha_inicio: date | datetime | None = Query(default=None),
    fecha_fin: date | datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> AuditLogListResponse:
    """CU-05: Consultar eventos de bitacora_auditoria con aislamiento por empresa y filtros."""
    res = await auditoria_service.listar_logs(
        current=current,
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(**res)

