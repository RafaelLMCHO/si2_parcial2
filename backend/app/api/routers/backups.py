from typing import Any
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser
from app.api.permissions import require_admin_or_superadmin
from app.controller.cu37_gestion_backups_controller import CU37GestionBackupsController
from app.schemas.backup import (
    BackupConfiguracionOut,
    BackupConfiguracionUpdate,
    BackupEstadisticasOut,
    BackupListResponse,
    BackupManualCreate,
    BackupModuloInfo,
    BackupRegistroOut,
    BackupRestaurarRequest,
)

router = APIRouter(prefix="/backups", tags=["CU-37 Gestión de Backups"])


@router.get("/modulos", response_model=list[BackupModuloInfo])
async def get_modulos_disponibles(
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> list[BackupModuloInfo]:
    """Obtiene los módulos y tablas disponibles para personalizar la copia de seguridad."""
    return CU37GestionBackupsController.modulos_disponibles(current)


@router.get("/estadisticas", response_model=BackupEstadisticasOut)
async def get_estadisticas(
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupEstadisticasOut:
    """Métricas agregadas de almacenamiento tanto en Localhost como en la Nube."""
    return await CU37GestionBackupsController.obtener_estadisticas(current)


@router.get("/configuracion", response_model=BackupConfiguracionOut)
async def get_configuracion(
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupConfiguracionOut:
    """Obtiene la configuración del backup automático programado."""
    return await CU37GestionBackupsController.obtener_configuracion_automatica(current)


@router.put("/configuracion", response_model=BackupConfiguracionOut)
async def update_configuracion(
    data: BackupConfiguracionUpdate,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupConfiguracionOut:
    """Guarda o actualiza la programación del backup automático."""
    return await CU37GestionBackupsController.guardar_configuracion_automatica(current, data)


@router.post("/configuracion/ejecutar-auto", response_model=list[str])
async def ejecutar_backup_auto_ahora(
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> list[str]:
    """Dispara inmediatamente la ejecución de la tarea de backup automático programada."""
    return await CU37GestionBackupsController.ejecutar_backup_automatico_ahora(current)


@router.get("", response_model=BackupListResponse)
async def list_backups(
    tipo: str | None = Query(default=None, pattern="^(manual|automatico)$"),
    destino: str | None = Query(default=None, pattern="^(local|nube)$"),
    search: str | None = Query(default=None, max_length=150),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupListResponse:
    """Lista las copias de seguridad generadas con filtros por tipo (manual/automático) y destino (local/nube)."""
    return await CU37GestionBackupsController.listar_backups(
        user=current,
        tipo=tipo,
        destino=destino,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=BackupRegistroOut, status_code=status.HTTP_201_CREATED)
async def create_backup(
    data: BackupManualCreate,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupRegistroOut:
    """Crea un backup personalizado manual seleccionando módulos/tablas, formato y destino (local/nube)."""
    return await CU37GestionBackupsController.crear_backup_manual(current, data)


@router.get("/{backup_id}", response_model=BackupRegistroOut)
async def get_backup_detalle(
    backup_id: str,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupRegistroOut:
    """Obtiene el detalle completo de un registro de backup."""
    return await CU37GestionBackupsController.obtener_backup(current, backup_id)


@router.get("/{backup_id}/download/{location}")
async def download_backup_file(
    backup_id: str,
    location: str,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> FileResponse:
    """Descarga el archivo físico del backup desde Localhost o simulado desde la Nube (AWS S3)."""
    from app.services.backup_service import BackupService
    path, filename, media_type = await BackupService.get_backup_file_data(
        current, backup_id, location=location
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Storage-Location": location,
        "X-Cloud-Provider": "AWS S3" if location == "cloud" else "Local Disk",
    }
    return FileResponse(path=path, filename=filename, media_type=media_type, headers=headers)


@router.post("/{backup_id}/sync-cloud", response_model=BackupRegistroOut)
async def sync_to_cloud(
    backup_id: str,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupRegistroOut:
    """Sincroniza una copia local a la Nube (AWS S3)."""
    return await CU37GestionBackupsController.sincronizar_a_nube(current, backup_id)


@router.post("/{backup_id}/sync-local", response_model=BackupRegistroOut)
async def sync_to_local(
    backup_id: str,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> BackupRegistroOut:
    """Descarga una copia desde la Nube a Localhost."""
    return await CU37GestionBackupsController.sincronizar_a_local(current, backup_id)


@router.post("/{backup_id}/restaurar")
async def restore_backup(
    backup_id: str,
    data: BackupRestaurarRequest,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> dict[str, Any]:
    """Restaura los datos contenidos en el backup hacia la base de datos."""
    return await CU37GestionBackupsController.restaurar_backup(current, backup_id, data)


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    current: CurrentUser = Depends(require_admin_or_superadmin),
) -> dict[str, Any]:
    """Elimina la copia de seguridad de la base de datos, del disco local y de la nube."""
    return await CU37GestionBackupsController.eliminar_backup(current, backup_id)

