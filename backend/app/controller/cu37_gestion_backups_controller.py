"""Controlador Backend para CU-37: Gestión de Backups (Personalizado, Automático y Manual).
Soporta persistencia, visibilidad y sincronización tanto en Localhost como en la Nube (AWS S3).
"""
from typing import Any
from asyncpg import Pool

from app.api.deps import CurrentUser
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
from app.services.backup_service import BackupService


class CU37GestionBackupsController:
    """Controlador que orquesta la generación de copias de seguridad manuales y automáticas,
    la personalización de módulos y tablas, y el almacenamiento híbrido Nube / Localhost.
    """

    @staticmethod
    def modulos_disponibles(user: CurrentUser) -> list[BackupModuloInfo]:
        is_superadmin = (user.rol == "superadmin")
        return BackupService.get_available_modules(is_superadmin=is_superadmin)

    @staticmethod
    async def listar_backups(
        user: CurrentUser,
        tipo: str | None = None,
        destino: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BackupListResponse:
        return await BackupService.list_backups(
            current_user=user,
            tipo=tipo,
            destino=destino,
            search=search,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    async def crear_backup_manual(
        user: CurrentUser,
        data: BackupManualCreate,
    ) -> BackupRegistroOut:
        return await BackupService.create_backup(
            current_user=user,
            data=data,
            tipo="manual",
        )

    @staticmethod
    async def obtener_configuracion_automatica(
        user: CurrentUser,
    ) -> BackupConfiguracionOut:
        is_superadmin = (user.rol == "superadmin")
        empresa_id = None if is_superadmin else user.empresa_id
        return await BackupService.get_configuracion(empresa_id=empresa_id)

    @staticmethod
    async def guardar_configuracion_automatica(
        user: CurrentUser,
        data: BackupConfiguracionUpdate,
    ) -> BackupConfiguracionOut:
        is_superadmin = (user.rol == "superadmin")
        empresa_id = None if is_superadmin else user.empresa_id
        return await BackupService.update_configuracion(
            empresa_id=empresa_id,
            data=data,
            current_user=user,
        )

    @staticmethod
    async def ejecutar_backup_automatico_ahora(
        user: CurrentUser,
    ) -> list[str]:
        is_superadmin = (user.rol == "superadmin")
        empresa_id = None if is_superadmin else user.empresa_id
        return await BackupService.run_scheduled_backups(force=True, force_empresa_id=empresa_id)

    @staticmethod
    async def obtener_estadisticas(
        user: CurrentUser,
    ) -> BackupEstadisticasOut:
        return await BackupService.get_estadisticas(current_user=user)

    @staticmethod
    async def obtener_backup(
        user: CurrentUser,
        backup_id: str,
    ) -> BackupRegistroOut:
        return await BackupService.get_backup(current_user=user, backup_id=backup_id)

    @staticmethod
    async def sincronizar_a_nube(
        user: CurrentUser,
        backup_id: str,
    ) -> BackupRegistroOut:
        return await BackupService.sync_to_cloud(current_user=user, backup_id=backup_id)

    @staticmethod
    async def sincronizar_a_local(
        user: CurrentUser,
        backup_id: str,
    ) -> BackupRegistroOut:
        return await BackupService.sync_to_local(current_user=user, backup_id=backup_id)

    @staticmethod
    async def restaurar_backup(
        user: CurrentUser,
        backup_id: str,
        data: BackupRestaurarRequest,
    ) -> dict[str, Any]:
        return await BackupService.restore_backup(
            current_user=user,
            backup_id=backup_id,
            data=data,
        )

    @staticmethod
    async def eliminar_backup(
        user: CurrentUser,
        backup_id: str,
    ) -> dict[str, Any]:
        return await BackupService.delete_backup(current_user=user, backup_id=backup_id)
