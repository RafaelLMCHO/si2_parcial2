"""Controlador Backend para CU-18: Disponibilidad en Tiendas / Búsqueda Omnicanal."""
from asyncpg import Pool
from app.services.inventario_service import InventarioService

class CU18DisponibilidadTiendasController:
    @staticmethod
    async def consultar_disponibilidad_variante(pool: Pool, empresa_id: str, variante_id: str):
        service = InventarioService(pool)
        return await service.consultar_disponibilidad_variante(empresa_id=empresa_id, variante_id=variante_id)

