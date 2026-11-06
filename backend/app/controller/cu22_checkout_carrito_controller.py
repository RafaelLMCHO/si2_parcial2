"""Controlador Backend para CU-22: Carrito de Compras y Checkout Omnicanal."""
from asyncpg import Pool
from app.services.carrito_service import CarritoService
from app.services.checkout_service import CheckoutService
from app.schemas.carrito import CarritoItemCreate
from app.schemas.venta import OrdenCheckoutCreate

class CU22CheckoutCarritoController:
    @staticmethod
    async def obtener_carrito(pool: Pool, empresa_id: str, cliente_id: str):
        service = CarritoService(pool)
        return await service.obtener_o_crear_carrito(empresa_id=empresa_id, cliente_id=cliente_id)

    @staticmethod
    async def agregar_item(pool: Pool, empresa_id: str, cliente_id: str, item: CarritoItemCreate):
        service = CarritoService(pool)
        return await service.agregar_item(empresa_id=empresa_id, cliente_id=cliente_id, item=item)

    @staticmethod
    async def crear_orden(pool: Pool, empresa_id: str, cliente_id: str, datos: OrdenCheckoutCreate):
        service = CheckoutService(pool)
        return await service.crear_orden(empresa_id=empresa_id, cliente_id=cliente_id, datos=datos)

