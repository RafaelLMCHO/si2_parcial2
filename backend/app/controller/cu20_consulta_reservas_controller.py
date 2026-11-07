"""Controlador Backend para CU-20: Consulta y Gestión de Reservas del Cliente."""
from asyncpg import Pool
from app.services.reserva_service import ReservaService

class CU20ConsultaReservasController:
    @staticmethod
    async def mis_reservas(pool: Pool, empresa_id: str, cliente_id: str):
        service = ReservaService(pool)
        return await service.mis_reservas(empresa_id=empresa_id, cliente_id=cliente_id)

    @staticmethod
    async def cancelar_reserva(pool: Pool, empresa_id: str, reserva_id: str, cliente_id: str, motivo: str = None):
        service = ReservaService(pool)
        return await service.cancelar_reserva(empresa_id=empresa_id, reserva_id=reserva_id, cliente_id=cliente_id, motivo=motivo)

