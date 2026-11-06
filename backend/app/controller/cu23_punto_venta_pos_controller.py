"""Controlador Backend para CU-23: Punto de Venta (POS) - Caja, Venta Rápida y Facturación."""
from asyncpg import Pool
from app.services.pos_service import PosService
from app.schemas.venta import VentaPosCreate

class CU23PuntoVentaPosController:
    @staticmethod
    async def buscar_por_barcode(pool: Pool, empresa_id: str, barcode: str):
        service = PosService(pool)
        return await service.buscar_variante_barcode(empresa_id=empresa_id, barcode=barcode)

    @staticmethod
    async def procesar_venta(pool: Pool, empresa_id: str, usuario_id: str, datos: VentaPosCreate):
        service = PosService(pool)
        return await service.procesar_venta_pos(empresa_id=empresa_id, usuario_id=usuario_id, datos=datos)

