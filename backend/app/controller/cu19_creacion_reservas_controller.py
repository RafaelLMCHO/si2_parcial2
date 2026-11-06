"""Controlador Backend para CU-19: Creación de Reservas y Probador."""
from asyncpg import Pool
from app.services.reserva_service import ReservaService
from app.schemas.reserva import ReservaCreate

class CU19CreacionReservasController:
    @staticmethod
    async def crear_reserva(pool: Pool, empresa_id: str, cliente_id: str, datos: ReservaCreate):
        service = ReservaService(pool)
        return await service.crear_reserva(empresa_id=empresa_id, cliente_id=cliente_id, datos=datos)

