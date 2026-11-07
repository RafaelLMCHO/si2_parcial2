"""Controlador Backend para CU-17: Gestión de Inventario, Kardex y Ajustes."""
from asyncpg import Pool
from app.services.inventario_service import InventarioService
from app.schemas.inventario import AjusteManualCreate

class CU17GestionInventarioController:
    @staticmethod
    async def listar_existencias(pool: Pool, empresa_id: str, sucursal_id: str = None, solo_bajo_minimo: bool = False):
        service = InventarioService(pool)
        return await service.listar_existencias(empresa_id=empresa_id, sucursal_id=sucursal_id, solo_bajo_minimo=solo_bajo_minimo)

    @staticmethod
    async def registrar_ajuste(pool: Pool, empresa_id: str, usuario_id: str, datos: AjusteManualCreate):
        service = InventarioService(pool)
        return await service.registrar_ajuste(empresa_id=empresa_id, usuario_id=usuario_id, datos=datos)

