"""Controlador Backend para CU-24: Procesamiento de Pagos, Pasarelas y Reembolsos."""
from asyncpg import Pool
from app.services.pago_service import PagoService
from app.schemas.pago import IntencionPagoCreate, ReembolsoCreate

class CU24ProcesamientoPagosController:
    @staticmethod
    async def crear_intencion_pago(pool: Pool, empresa_id: str, datos: IntencionPagoCreate):
        service = PagoService(pool)
        return await service.crear_intencion_pago(empresa_id=empresa_id, datos=datos)

    @staticmethod
    async def consultar_pago(pool: Pool, empresa_id: str, pago_id: str):
        service = PagoService(pool)
        return await service.consultar_pago(empresa_id=empresa_id, pago_id=pago_id)

    @staticmethod
    async def solicitar_reembolso(pool: Pool, empresa_id: str, pago_id: str, datos: ReembolsoCreate):
        service = PagoService(pool)
        return await service.solicitar_reembolso(empresa_id=empresa_id, pago_id=pago_id, datos=datos)

