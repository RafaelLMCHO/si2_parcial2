"""Controlador Backend para CU-29: Validar Comprobante y Procesar Cambio mediante QR Offline."""
from asyncpg import Pool
from app.services.sync_service import SyncService
from app.schemas.sync import NotaCambioCreate

class CU29ValidarQrCambioOfflineController:
    @staticmethod
    async def validar_qr(pool: Pool, empresa_id: str, qr_data: str):
        service = SyncService(pool)
        return await service.validar_qr_comprobante(empresa_id=empresa_id, qr_data=qr_data)

    @staticmethod
    async def emitir_nota_cambio(pool: Pool, empresa_id: str, usuario_id: str, datos: NotaCambioCreate):
        service = SyncService(pool)
        return await service.procesar_nota_cambio(empresa_id=empresa_id, usuario_id=usuario_id, datos=datos)

