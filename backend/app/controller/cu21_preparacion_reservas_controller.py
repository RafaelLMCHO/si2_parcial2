"""Controlador Backend para CU-21: Preparación y Validación de Reservas en Tienda (Staff)."""
from asyncpg import Pool
from app.services.reserva_service import ReservaService

class CU21PreparacionReservasController:
    @staticmethod
    async def listar_reservas_sucursal(pool: Pool, empresa_id: str, sucursal_id: str, estado: str = None):
        service = ReservaService(pool)
        return await service.listar_reservas(empresa_id=empresa_id, sucursal_id=sucursal_id, estado=estado)

    @staticmethod
    async def preparar_reserva(pool: Pool, empresa_id: str, reserva_id: str, usuario_id: str):
        service = ReservaService(pool)
        return await service.preparar_reserva(empresa_id=empresa_id, reserva_id=reserva_id, usuario_id=usuario_id)

    @staticmethod
    async def completar_reserva(pool: Pool, empresa_id: str, reserva_id: str, usuario_id: str):
        service = ReservaService(pool)
        return await service.completar_reserva(empresa_id=empresa_id, reserva_id=reserva_id, usuario_id=usuario_id)

    @staticmethod
    async def registrar_incidencia(pool: Pool, empresa_id: str, reserva_id: str, usuario_id: str, detalle: str):
        service = ReservaService(pool)
        return await service.registrar_incidencia(empresa_id=empresa_id, reserva_id=reserva_id, usuario_id=usuario_id, detalle=detalle)

