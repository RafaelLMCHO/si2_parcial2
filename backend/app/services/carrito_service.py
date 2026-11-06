"""
Servicio de Carrito de Compras (CU-22).
Gestiona el carrito activo por usuario/tenant.
"""
import logging
from decimal import Decimal
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------

async def _get_or_create_carrito(conn, empresa_id: str, user_id: str) -> str:
    """Obtiene o crea el carrito activo del usuario."""
    carrito_id = await conn.fetchval(
        "SELECT id FROM carrito WHERE empresa_id=$1 AND usuario_id=$2 AND estado='activo' LIMIT 1",
        UUID(empresa_id), UUID(user_id),
    )
    if carrito_id is None:
        carrito_id = await conn.fetchval(
            "INSERT INTO carrito (empresa_id, usuario_id, estado) VALUES ($1,$2,'activo') RETURNING id",
            UUID(empresa_id), UUID(user_id),
        )
    return str(carrito_id)


async def _load_carrito(conn, carrito_id: str, empresa_id: str) -> dict:
    """Carga el carrito con todos sus items (JOIN completo)."""
    carrito_row = await conn.fetchrow(
        """
        SELECT c.id, c.empresa_id, c.usuario_id, c.estado, c.created_at, c.updated_at
          FROM carrito c
         WHERE c.id = $1 AND c.empresa_id = $2
        """,
        UUID(carrito_id), UUID(empresa_id),
    )
    if carrito_row is None:
        raise api_error(404, "CARRITO_NO_ENCONTRADO", "El carrito no existe")

    items_rows = await conn.fetch(
        """
        SELECT cd.id,
               cd.variante_id,
               v.sku,
               p.nombre AS prenda_nombre,
               ta.nombre AS talla,
               co.nombre AS color,
               p.imagen_url,
               cd.cantidad,
               cd.precio_unitario,
               (cd.cantidad * cd.precio_unitario) AS subtotal
          FROM carrito_detalle cd
          JOIN variante v ON v.id = cd.variante_id
          JOIN prenda p ON p.id = v.prenda_id
          JOIN talla ta ON ta.id = v.talla_id
          JOIN color co ON co.id = v.color_id
         WHERE cd.carrito_id = $1 AND cd.empresa_id = $2
         ORDER BY cd.created_at ASC
        """,
        UUID(carrito_id), UUID(empresa_id),
    )

    items = [
        {
            "id": str(r["id"]),
            "variante_id": str(r["variante_id"]),
            "sku": r["sku"],
            "prenda_nombre": r["prenda_nombre"],
            "talla": r["talla"],
            "color": r["color"],
            "imagen_url": r["imagen_url"],
            "cantidad": r["cantidad"],
            "precio_unitario": r["precio_unitario"],
            "subtotal": r["subtotal"],
        }
        for r in items_rows
    ]

    total = sum(Decimal(str(i["subtotal"])) for i in items)

    return {
        "id": str(carrito_row["id"]),
        "empresa_id": str(carrito_row["empresa_id"]),
        "usuario_id": str(carrito_row["usuario_id"]) if carrito_row["usuario_id"] else None,
        "estado": carrito_row["estado"],
        "items": items,
        "total": total,
        "created_at": carrito_row["created_at"],
        "updated_at": carrito_row["updated_at"],
    }


# ---------------------------------------------------------------------------
# Endpoints públicos
# ---------------------------------------------------------------------------

async def get_carrito(empresa_id: str, user_id: str) -> dict:
    """Obtiene (o crea) el carrito activo del usuario con todos sus items."""
    async with tenant_connection(empresa_id, user_id) as conn:
        carrito_id = await _get_or_create_carrito(conn, empresa_id, user_id)
        return await _load_carrito(conn, carrito_id, empresa_id)


async def add_item(empresa_id: str, user_id: str, variante_id: str, cantidad: int) -> dict:
    """
    Agrega un ítem al carrito.
    - Valida que la variante pertenece al tenant y está activa.
    - Si la variante ya existe en el carrito, suma las cantidades.
    - Captura precio_unitario = variante.precio_venta actual.
    """
    if cantidad <= 0:
        raise api_error(422, "CANTIDAD_INVALIDA", "La cantidad debe ser mayor a cero")

    async with tenant_connection(empresa_id, user_id) as conn:
        # Validar variante en tenant
        variante = await conn.fetchrow(
            """
            SELECT v.id, v.precio_venta, v.estado
              FROM variante v
             WHERE v.id = $1 AND v.empresa_id = $2 AND v.deleted_at IS NULL
            """,
            UUID(variante_id), UUID(empresa_id),
        )
        if variante is None:
            raise api_error(404, "VARIANTE_NO_ENCONTRADA", "La variante no existe en este tenant")
        if variante["estado"] != "activa":
            raise api_error(422, "VARIANTE_INACTIVA", "La variante no está disponible para venta")

        precio_unitario = variante["precio_venta"]
        carrito_id = await _get_or_create_carrito(conn, empresa_id, user_id)

        # ¿Ya existe este ítem en el carrito?
        existing = await conn.fetchrow(
            """
            SELECT id, cantidad FROM carrito_detalle
             WHERE carrito_id = $1 AND variante_id = $2 AND empresa_id = $3
            """,
            UUID(carrito_id), UUID(variante_id), UUID(empresa_id),
        )
        if existing is not None:
            nueva_cantidad = existing["cantidad"] + cantidad
            await conn.execute(
                """
                UPDATE carrito_detalle
                   SET cantidad = $1, precio_unitario = $2, updated_at = now()
                 WHERE id = $3
                """,
                nueva_cantidad, precio_unitario, existing["id"],
            )
        else:
            await conn.execute(
                """
                INSERT INTO carrito_detalle (empresa_id, carrito_id, variante_id, cantidad, precio_unitario)
                VALUES ($1, $2, $3, $4, $5)
                """,
                UUID(empresa_id), UUID(carrito_id), UUID(variante_id), cantidad, precio_unitario,
            )

        # Actualizar timestamp del carrito
        await conn.execute(
            "UPDATE carrito SET updated_at = now() WHERE id = $1",
            UUID(carrito_id),
        )
        return await _load_carrito(conn, carrito_id, empresa_id)


async def update_item(empresa_id: str, user_id: str, item_id: str, cantidad: int) -> dict:
    """
    Actualiza la cantidad de un ítem del carrito del usuario.
    Valida que el ítem pertenece al carrito activo del usuario.
    """
    if cantidad <= 0:
        raise api_error(422, "CANTIDAD_INVALIDA", "La cantidad debe ser mayor a cero")

    async with tenant_connection(empresa_id, user_id) as conn:
        carrito_id = await conn.fetchval(
            "SELECT id FROM carrito WHERE empresa_id=$1 AND usuario_id=$2 AND estado='activo' LIMIT 1",
            UUID(empresa_id), UUID(user_id),
        )
        if carrito_id is None:
            raise api_error(404, "CARRITO_NO_ENCONTRADO", "No hay carrito activo")

        item = await conn.fetchrow(
            """
            SELECT id FROM carrito_detalle
             WHERE id = $1 AND carrito_id = $2 AND empresa_id = $3
            """,
            UUID(item_id), carrito_id, UUID(empresa_id),
        )
        if item is None:
            raise api_error(404, "ITEM_NO_ENCONTRADO", "El ítem no existe en el carrito del usuario")

        await conn.execute(
            "UPDATE carrito_detalle SET cantidad = $1, updated_at = now() WHERE id = $2",
            cantidad, UUID(item_id),
        )
        await conn.execute(
            "UPDATE carrito SET updated_at = now() WHERE id = $1",
            carrito_id,
        )
        return await _load_carrito(conn, str(carrito_id), empresa_id)


async def remove_item(empresa_id: str, user_id: str, item_id: str) -> dict:
    """
    Elimina un ítem del carrito del usuario.
    Valida que el ítem pertenece al carrito activo del usuario.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        carrito_id = await conn.fetchval(
            "SELECT id FROM carrito WHERE empresa_id=$1 AND usuario_id=$2 AND estado='activo' LIMIT 1",
            UUID(empresa_id), UUID(user_id),
        )
        if carrito_id is None:
            raise api_error(404, "CARRITO_NO_ENCONTRADO", "No hay carrito activo")

        result = await conn.execute(
            """
            DELETE FROM carrito_detalle
             WHERE id = $1 AND carrito_id = $2 AND empresa_id = $3
            """,
            UUID(item_id), carrito_id, UUID(empresa_id),
        )
        if result == "DELETE 0":
            raise api_error(404, "ITEM_NO_ENCONTRADO", "El ítem no existe en el carrito del usuario")

        await conn.execute(
            "UPDATE carrito SET updated_at = now() WHERE id = $1",
            carrito_id,
        )
        return await _load_carrito(conn, str(carrito_id), empresa_id)


class CarritoService:
    def __init__(self, pool=None):
        self.pool = pool

    async def obtener_o_crear_carrito(self, empresa_id: str, cliente_id: str):
        return await get_carrito(empresa_id=empresa_id, user_id=cliente_id)

    async def agregar_item(self, empresa_id: str, cliente_id: str, item=None):
        return await add_item(empresa_id=empresa_id, user_id=cliente_id, req=item)
