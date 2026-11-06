"""
Servicio de Inventario — CU-17 (Gestión de Stock) y CU-18 (Transferencias)
==========================================================================

Convenciones del proyecto:
- asyncpg raw SQL, sin ORM
- tenant_connection(empresa_id, user_id) → context-manager que abre transacción
- audit_event(...)                         → escritura de auditoría fuera de la tx
- api_error(status, code, message)         → raise HTTPException uniforme
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HELPERS INTERNOS
# ---------------------------------------------------------------------------

def _uuid(val: str | UUID) -> UUID:
    """Convierte str → UUID de forma segura."""
    return UUID(str(val)) if not isinstance(val, UUID) else val


def _maybe_uuid(val: str | UUID | None) -> UUID | None:
    """Convierte a UUID solo si el valor es válido; las referencias libres se ignoran."""
    if val is None:
        return None
    if isinstance(val, UUID):
        return val
    try:
        return UUID(str(val))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# FUNCIONES PÚBLICAS DEL SERVICIO
# (Reciben una conexión abierta — NO hacen commit)
# ---------------------------------------------------------------------------


async def registrar_movimiento(
    conn,
    empresa_id: str,
    variante_id: str,
    sucursal_id: str,
    tipo: str,
    cantidad: int,
    stock_anterior: int,
    stock_nuevo: int,
    usuario_id: str | None = None,
    motivo: str | None = None,
    referencia_tipo: str | None = None,
    referencia_id: str | None = None,
) -> None:
    """Inserta una fila en movimiento_inventario (tabla particionada)."""
    await conn.execute(
        """
        INSERT INTO movimiento_inventario (
            empresa_id, variante_id, sucursal_id,
            tipo, cantidad, stock_anterior, stock_nuevo,
            referencia_tipo, referencia_id,
            motivo, usuario_id, ocurrido_en
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, now())
        """,
        _uuid(empresa_id),
        _uuid(variante_id),
        _uuid(sucursal_id),
        tipo,
        cantidad,
        stock_anterior,
        stock_nuevo,
        referencia_tipo,
        _maybe_uuid(referencia_id),
        motivo,
        _uuid(usuario_id) if usuario_id else None,
    )


async def reservar_stock(
    conn,
    empresa_id: str,
    sucursal_id: str,
    items: list[dict],  # [{variante_id, cantidad}]
    usuario_id: str,
    referencia_tipo: str | None = None,
    referencia_id: str | None = None,
) -> None:
    """
    Incrementa stock_reservado para cada item.
    Asume que la disponibilidad ya fue verificada y las filas bloqueadas (FOR UPDATE).
    NO registra movimiento de kárdex (solo cambia stock_reservado).
    """
    for item in items:
        vid = _uuid(item["variante_id"])
        cant = int(item["cantidad"])

        await conn.execute(
            """
            UPDATE inventario
               SET stock_reservado = stock_reservado + $1,
                   actualizado_en  = now()
             WHERE empresa_id  = $2
               AND variante_id = $3
               AND sucursal_id = $4
            """,
            cant,
            _uuid(empresa_id),
            vid,
            _uuid(sucursal_id),
        )


async def liberar_stock_reservado(
    conn,
    empresa_id: str,
    sucursal_id: str,
    items: list[dict],  # [{variante_id, cantidad}]
    usuario_id: str,
    motivo: str = "Cancelación de reserva",
) -> None:
    """
    Decrementa stock_reservado.
    NO toca stock_fisico y NO escribe en movimiento_inventario
    (la tabla reserva_estado_historial documenta el cambio).
    """
    for item in items:
        vid = _uuid(item["variante_id"])
        cant = int(item["cantidad"])

        await conn.execute(
            """
            UPDATE inventario
               SET stock_reservado = GREATEST(stock_reservado - $1, 0),
                   actualizado_en  = now()
             WHERE empresa_id  = $2
               AND variante_id = $3
               AND sucursal_id = $4
            """,
            cant,
            _uuid(empresa_id),
            vid,
            _uuid(sucursal_id),
        )


async def descontar_stock_venta(
    conn,
    empresa_id: str,
    sucursal_id: str,
    items: list[dict],  # [{variante_id, cantidad}]
    usuario_id: str,
    referencia_tipo: str = "venta",
    referencia_id: str | None = None,
    motivo: str = "Venta",
) -> None:
    """
    Descuenta stock_fisico (y si hay stock_reservado de esta variante, también lo reduce).
    Registra movimiento tipo 'venta' en kárdex.
    Lanza 409 si stock insuficiente.
    """
    for item in items:
        vid = _uuid(item["variante_id"])
        cant = int(item["cantidad"])

        row = await conn.fetchrow(
            """
            SELECT stock_fisico, stock_reservado
              FROM inventario
             WHERE empresa_id  = $1
               AND variante_id = $2
               AND sucursal_id = $3
            FOR UPDATE
            """,
            _uuid(empresa_id),
            vid,
            _uuid(sucursal_id),
        )

        if row is None:
            raise api_error(
                409,
                "STOCK_INSUFICIENTE",
                f"No existe registro de inventario para variante {item['variante_id']}",
            )

        stock_fisico = int(row["stock_fisico"])
        stock_reservado = int(row["stock_reservado"])

        if stock_fisico < cant:
            raise api_error(
                409,
                "STOCK_INSUFICIENTE",
                f"Stock insuficiente para variante {item['variante_id']}: "
                f"disponible={stock_fisico}, solicitado={cant}",
            )

        # Reducir reservado en la misma cantidad si lo hay
        reduccion_reservado = min(stock_reservado, cant)
        stock_nuevo = stock_fisico - cant

        await conn.execute(
            """
            UPDATE inventario
               SET stock_fisico    = stock_fisico    - $1,
                   stock_reservado = GREATEST(stock_reservado - $2, 0),
                   actualizado_en  = now()
             WHERE empresa_id  = $3
               AND variante_id = $4
               AND sucursal_id = $5
            """,
            cant,
            reduccion_reservado,
            _uuid(empresa_id),
            vid,
            _uuid(sucursal_id),
        )

        await registrar_movimiento(
            conn,
            empresa_id=empresa_id,
            variante_id=str(vid),
            sucursal_id=sucursal_id,
            tipo="venta",
            cantidad=-cant,
            stock_anterior=stock_fisico,
            stock_nuevo=stock_nuevo,
            usuario_id=usuario_id,
            motivo=motivo,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
        )


# ---------------------------------------------------------------------------
# FUNCIONES DE ENDPOINTS
# (Abren su propia transacción con tenant_connection)
# ---------------------------------------------------------------------------


async def listar_inventario(
    empresa_id: str,
    user_id: str,
    rol: str,
    sucursal_id_filtro: str | None = None,
    encargado_sucursal_id: str | None = None,
    prenda_id: str | None = None,
    q: str | None = None,
    solo_bajo_minimo: bool = False,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Listado paginado del inventario.
    - encargado_sucursal_id: si el usuario es encargado, fuerza el filtro a su sucursal.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        conditions: list[str] = ["i.empresa_id = $1", "v.deleted_at IS NULL"]
        params: list[object] = [_uuid(empresa_id)]

        # El encargado solo ve su sucursal
        efectiva_sucursal = sucursal_id_filtro
        if encargado_sucursal_id:
            efectiva_sucursal = encargado_sucursal_id

        if efectiva_sucursal:
            params.append(_uuid(efectiva_sucursal))
            conditions.append(f"i.sucursal_id = ${len(params)}")

        if prenda_id:
            params.append(_uuid(prenda_id))
            conditions.append(f"v.prenda_id = ${len(params)}")

        if q:
            params.append(f"%{q.strip().lower()}%")
            idx = len(params)
            conditions.append(
                f"(lower(p.nombre) LIKE ${idx} OR lower(p.codigo) LIKE ${idx} "
                f"OR lower(v.sku) LIKE ${idx} OR lower(COALESCE(v.codigo_barras,'')) LIKE ${idx})"
            )

        if solo_bajo_minimo:
            conditions.append("i.stock_disponible <= i.stock_minimo")

        where = " AND ".join(conditions)

        total: int = await conn.fetchval(
            f"""
            SELECT count(*)::integer
              FROM inventario i
              JOIN variante v ON v.id = i.variante_id AND v.empresa_id = i.empresa_id
              JOIN prenda p   ON p.id = v.prenda_id
              JOIN sucursal s ON s.id = i.sucursal_id AND s.empresa_id = i.empresa_id
             WHERE {where}
            """,
            *params,
        )

        limit  = page_size
        offset = (page - 1) * page_size
        params.extend([limit, offset])

        rows = await conn.fetch(
            f"""
            SELECT i.id,
                   i.empresa_id,
                   i.variante_id,
                   i.sucursal_id,
                   s.nombre          AS sucursal_nombre,
                   i.stock_fisico,
                   i.stock_reservado,
                   i.stock_disponible,
                   i.stock_minimo,
                   i.ubicacion,
                   i.actualizado_en,
                   v.sku,
                   v.codigo_barras,
                   v.precio_venta,
                   v.prenda_id,
                   p.nombre          AS prenda_nombre,
                   p.codigo          AS prenda_codigo,
                   t.nombre          AS talla_nombre,
                   c.nombre          AS color_nombre,
                   c.hex             AS color_hex
              FROM inventario i
              JOIN variante v ON v.id = i.variante_id AND v.empresa_id = i.empresa_id
              JOIN prenda p   ON p.id = v.prenda_id
              JOIN sucursal s ON s.id = i.sucursal_id AND s.empresa_id = i.empresa_id
              JOIN talla t    ON t.id = v.talla_id
              JOIN color c    ON c.id = v.color_id
             WHERE {where}
             ORDER BY s.nombre, p.nombre, t.orden, c.nombre
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

        agrupados: dict[str, dict] = {}
        for r in rows:
            vid = str(r["variante_id"])
            if vid not in agrupados:
                agrupados[vid] = {
                    "variante_id": r["variante_id"],
                    "sku": r["sku"],
                    "codigo_barras": r["codigo_barras"],
                    "prenda_id": r["prenda_id"],
                    "prenda_nombre": r["prenda_nombre"],
                    "talla": r["talla_nombre"],
                    "color": r["color_nombre"],
                    "precio_venta": r["precio_venta"],
                    "existencias": [],
                }
            agrupados[vid]["existencias"].append({
                "inventario_id": r["id"],
                "sucursal_id": r["sucursal_id"],
                "sucursal_nombre": r["sucursal_nombre"],
                "stock_fisico": r["stock_fisico"],
                "stock_reservado": r["stock_reservado"],
                "stock_disponible": r["stock_disponible"],
                "stock_minimo": r["stock_minimo"],
                "ubicacion": r["ubicacion"],
                "bajo_minimo": int(r["stock_disponible"]) <= int(r["stock_minimo"]),
                "actualizado_en": r["actualizado_en"],
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-total // page_size)),
            "items": list(agrupados.values()),
        }


async def registrar_ingreso(
    empresa_id: str,
    user_id: str,
    sucursal_id: str,
    items: list,  # [{variante_id, cantidad}]
    motivo: str,
    referencia: str | None = None,
) -> dict:
    """
    Registra un ingreso de mercadería (tipo 'entrada') para una sucursal.
    Hace UPSERT en inventario y escribe en movimiento_inventario.
    """
    if not items:
        raise api_error(422, "ITEMS_REQUERIDOS", "Debe proporcionar al menos un item")

    resultados: list[dict] = []

    async with tenant_connection(empresa_id, user_id) as conn:
        # Verificar que la sucursal pertenece al tenant
        suc = await conn.fetchrow(
            "SELECT id, nombre, estado FROM sucursal WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            _uuid(sucursal_id),
            _uuid(empresa_id),
        )
        if suc is None:
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal no existe")
        if suc["estado"] != "activa":
            raise api_error(409, "SUCURSAL_INACTIVA", "La sucursal no está activa")

        for item in items:
            vid = _uuid(item["variante_id"])
            cant = int(item["cantidad"])

            if cant <= 0:
                raise api_error(422, "CANTIDAD_INVALIDA", "La cantidad debe ser mayor a cero")

            # Verificar variante en tenant
            var_ok = await conn.fetchval(
                "SELECT id FROM variante WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
                vid,
                _uuid(empresa_id),
            )
            if var_ok is None:
                raise api_error(404, "VARIANTE_NO_ENCONTRADA", f"La variante {item['variante_id']} no existe")

            # UPSERT inventario
            row = await conn.fetchrow(
                """
                INSERT INTO inventario (empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo, actualizado_en)
                VALUES ($1, $2, $3, $4, 0, 0, now())
                ON CONFLICT (empresa_id, variante_id, sucursal_id)
                DO UPDATE SET
                    stock_fisico   = inventario.stock_fisico + EXCLUDED.stock_fisico,
                    actualizado_en = now()
                RETURNING id, stock_fisico, stock_reservado
                """,
                _uuid(empresa_id),
                vid,
                _uuid(sucursal_id),
                cant,
            )

            stock_nuevo    = int(row["stock_fisico"])
            stock_anterior = stock_nuevo - cant

            await registrar_movimiento(
                conn,
                empresa_id=empresa_id,
                variante_id=str(vid),
                sucursal_id=sucursal_id,
                tipo="entrada",
                cantidad=cant,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                usuario_id=user_id,
                motivo=motivo,
                referencia_tipo="ingreso",
                referencia_id=referencia,
            )

            resultados.append({
                "variante_id": str(vid),
                "cantidad_ingresada": cant,
                "stock_nuevo": stock_nuevo,
            })

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="inventario_ingreso",
        entidad_id=sucursal_id,
        datos_despues={"sucursal_id": sucursal_id, "motivo": motivo, "items": resultados},
    )

    return {
        "ok": True,
        "mensaje": "Ingreso registrado correctamente",
        "sucursal_id": sucursal_id,
        "items": resultados,
        "ingresados": len(resultados),
    }


async def registrar_ajuste(
    empresa_id: str,
    user_id: str,
    sucursal_id: str,
    variante_id: str,
    cantidad: int,
    motivo: str,
    referencia: str | None = None,
) -> dict:
    """
    Ajuste de inventario positivo (+) o negativo (−).
    - cantidad < 0: merma — verifica que stock_fisico + cantidad >= stock_reservado
    - Lanza 409 con maximo_ajuste_negativo si no es viable.
    """
    if cantidad == 0:
        raise api_error(422, "CANTIDAD_INVALIDA", "La cantidad del ajuste no puede ser cero")

    async with tenant_connection(empresa_id, user_id) as conn:
        # Verificar sucursal
        suc = await conn.fetchrow(
            "SELECT id, estado FROM sucursal WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            _uuid(sucursal_id),
            _uuid(empresa_id),
        )
        if suc is None:
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal no existe")
        if suc["estado"] != "activa":
            raise api_error(409, "SUCURSAL_INACTIVA", "La sucursal no está activa")

        # Verificar variante
        var_ok = await conn.fetchval(
            "SELECT id FROM variante WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            _uuid(variante_id),
            _uuid(empresa_id),
        )
        if var_ok is None:
            raise api_error(404, "VARIANTE_NO_ENCONTRADA", f"La variante {variante_id} no existe")

        # Obtener inventario actual con bloqueo
        inv = await conn.fetchrow(
            """
            SELECT id, stock_fisico, stock_reservado
              FROM inventario
             WHERE empresa_id  = $1
               AND variante_id = $2
               AND sucursal_id = $3
            FOR UPDATE
            """,
            _uuid(empresa_id),
            _uuid(variante_id),
            _uuid(sucursal_id),
        )

        if inv is None:
            # Si es merma y no hay inventario, rechazar
            if cantidad < 0:
                raise api_error(
                    409,
                    "STOCK_INSUFICIENTE",
                    "No existe registro de inventario para esta variante en la sucursal",
                )
            # Si es entrada sin registro previo, crearlo
            stock_anterior = 0
            stock_nuevo    = cantidad
            await conn.execute(
                """
                INSERT INTO inventario (empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo, actualizado_en)
                VALUES ($1, $2, $3, $4, 0, 0, now())
                """,
                _uuid(empresa_id),
                _uuid(variante_id),
                _uuid(sucursal_id),
                cantidad,
            )
        else:
            stock_fisico    = int(inv["stock_fisico"])
            stock_reservado = int(inv["stock_reservado"])
            stock_anterior  = stock_fisico
            stock_nuevo     = stock_fisico + cantidad

            # Validar merma
            if cantidad < 0:
                if stock_nuevo < 0:
                    raise api_error(
                        409,
                        "STOCK_INSUFICIENTE",
                        f"El ajuste dejaría stock negativo. "
                        f"Stock actual: {stock_fisico}, ajuste: {cantidad}",
                    )
                if stock_nuevo < stock_reservado:
                    max_negativo = -(stock_fisico - stock_reservado)
                    raise api_error(
                        409,
                        "STOCK_INSUFICIENTE",
                        f"El ajuste dejaría stock_fisico ({stock_nuevo}) "
                        f"por debajo de stock_reservado ({stock_reservado}). "
                        f"Máximo ajuste negativo permitido: {max_negativo}",
                    )

            await conn.execute(
                """
                UPDATE inventario
                   SET stock_fisico   = stock_fisico + $1,
                       actualizado_en = now()
                 WHERE empresa_id  = $2
                   AND variante_id = $3
                   AND sucursal_id = $4
                """,
                cantidad,
                _uuid(empresa_id),
                _uuid(variante_id),
                _uuid(sucursal_id),
            )

        tipo_movimiento = "ajuste"
        await registrar_movimiento(
            conn,
            empresa_id=empresa_id,
            variante_id=variante_id,
            sucursal_id=sucursal_id,
            tipo=tipo_movimiento,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            usuario_id=user_id,
            motivo=motivo,
            referencia_tipo="ajuste",
            referencia_id=referencia,
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="inventario_ajuste",
        entidad_id=variante_id,
        datos_antes={"stock_fisico": stock_anterior},
        datos_despues={
            "variante_id": variante_id,
            "sucursal_id": sucursal_id,
            "cantidad": cantidad,
            "motivo": motivo,
            "stock_nuevo": stock_nuevo,
        },
    )

    return {
        "mensaje": "Ajuste registrado correctamente",
        "variante_id": variante_id,
        "sucursal_id": sucursal_id,
        "cantidad": cantidad,
        "stock_anterior": stock_anterior,
        "stock_nuevo": stock_nuevo,
    }


async def crear_transferencia(
    empresa_id: str,
    user_id: str,
    origen_id: str,
    destino_id: str,
    items: list,  # [{variante_id, cantidad}]
    motivo: str | None = None,
) -> dict:
    """
    Crea y ejecuta inmediatamente una transferencia de stock entre sucursales.
    Todo en UNA transacción con tenant_connection.

    Pasos:
    1. Validar origen != destino
    2. Verificar ambas sucursales en el tenant y activas
    3. SELECT ... FOR UPDATE de filas inventario en orden determinístico
    4. Verificar stock_disponible >= cantidad para cada item
    5. INSERT transferencia_inventario (estado='recibida')
    6. INSERT transferencia_detalle
    7. UPDATE inventario origen (−)
    8. UPSERT inventario destino (+)
    9. registrar_movimiento transferencia_salida / transferencia_entrada
    10. Auditoría
    """
    if not items:
        raise api_error(422, "ITEMS_REQUERIDOS", "Debe proporcionar al menos un item")

    if origen_id == destino_id:
        raise api_error(
            422,
            "SUCURSALES_IGUALES",
            "La sucursal de origen y destino no pueden ser la misma",
        )

    transferencia_id: UUID | None = None
    stock_antes_origen: dict[str, int] = {}

    async with tenant_connection(empresa_id, user_id) as conn:
        # --- 2. Verificar sucursales ---
        for suc_id, label in [(origen_id, "origen"), (destino_id, "destino")]:
            suc = await conn.fetchrow(
                "SELECT id, nombre, estado, empresa_id FROM sucursal WHERE id = $1 AND deleted_at IS NULL",
                _uuid(suc_id),
            )
            if suc is None:
                raise api_error(404, "SUCURSAL_NO_ENCONTRADA", f"La sucursal de {label} no existe")
            if str(suc["empresa_id"]) != str(empresa_id):
                raise api_error(
                    403,
                    "AISLAMIENTO_TENANT",
                    f"La sucursal de {label} no pertenece a la empresa",
                )
            if suc["estado"] != "activa":
                raise api_error(
                    409,
                    "SUCURSAL_INACTIVA",
                    f"La sucursal de {label} no está activa",
                )

        # --- 3. Bloquear filas de inventario en orden determinístico ---
        # Ordenar por (sucursal_id, variante_id) para evitar deadlocks
        pares_origen  = sorted(
            [(_uuid(origen_id), _uuid(item["variante_id"])) for item in items],
            key=lambda x: (str(x[0]), str(x[1])),
        )

        # Verificar variantes en tenant
        for _, vid in pares_origen:
            var_ok = await conn.fetchval(
                "SELECT id FROM variante WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
                vid,
                _uuid(empresa_id),
            )
            if var_ok is None:
                raise api_error(404, "VARIANTE_NO_ENCONTRADA", f"La variante {vid} no existe")

        # Bloquear inventario origen
        inv_rows = await conn.fetch(
            """
            SELECT variante_id, stock_fisico, stock_reservado, stock_disponible
              FROM inventario
             WHERE empresa_id  = $1
               AND sucursal_id = $2
               AND variante_id = ANY($3::uuid[])
             ORDER BY sucursal_id, variante_id
            FOR UPDATE
            """,
            _uuid(empresa_id),
            _uuid(origen_id),
            [vid for _, vid in pares_origen],
        )

        inv_map: dict[str, dict] = {str(r["variante_id"]): r for r in inv_rows}

        # --- 4. Verificar disponibilidad ---
        faltantes: list[dict] = []
        for item in items:
            vid_str = str(_uuid(item["variante_id"]))
            cant    = int(item["cantidad"])
            if cant <= 0:
                raise api_error(422, "CANTIDAD_INVALIDA", "La cantidad debe ser mayor a cero")

            inv = inv_map.get(vid_str)
            disponible = int(inv["stock_disponible"]) if inv else 0

            if inv is None or disponible < cant:
                faltantes.append({
                    "variante_id": vid_str,
                    "solicitado": cant,
                    "maximo_disponible": disponible,
                })

        if faltantes:
            raise api_error(
                409,
                "STOCK_INSUFICIENTE",
                "Stock insuficiente para uno o más items de la transferencia",
            )

        # --- 5. INSERT transferencia_inventario ---
        trans_row = await conn.fetchrow(
            """
            INSERT INTO transferencia_inventario (
                empresa_id, origen_id, destino_id, estado, solicitada_por
            )
            VALUES ($1, $2, $3, 'recibida', $4)
            RETURNING id
            """,
            _uuid(empresa_id),
            _uuid(origen_id),
            _uuid(destino_id),
            _uuid(user_id),
        )
        transferencia_id = trans_row["id"]

        # --- 6-9. Por cada item ---
        for item in items:
            vid  = _uuid(item["variante_id"])
            cant = int(item["cantidad"])
            vid_str = str(vid)

            inv_origen = inv_map[vid_str]
            sf_antes   = int(inv_origen["stock_fisico"])
            sf_origen_nuevo = sf_antes - cant
            stock_antes_origen[vid_str] = sf_antes

            # 6. INSERT transferencia_detalle
            await conn.execute(
                """
                INSERT INTO transferencia_detalle (
                    empresa_id, transferencia_id, variante_id, cantidad, cantidad_recibida
                )
                VALUES ($1, $2, $3, $4, $4)
                """,
                _uuid(empresa_id),
                transferencia_id,
                vid,
                cant,
            )

            # 7. UPDATE inventario origen
            await conn.execute(
                """
                UPDATE inventario
                   SET stock_fisico   = stock_fisico - $1,
                       actualizado_en = now()
                 WHERE empresa_id  = $2
                   AND variante_id = $3
                   AND sucursal_id = $4
                """,
                cant,
                _uuid(empresa_id),
                vid,
                _uuid(origen_id),
            )

            # 8. UPSERT inventario destino
            dest_row = await conn.fetchrow(
                """
                INSERT INTO inventario (
                    empresa_id, variante_id, sucursal_id,
                    stock_fisico, stock_reservado, stock_minimo, actualizado_en
                )
                VALUES ($1, $2, $3, $4, 0, 0, now())
                ON CONFLICT (empresa_id, variante_id, sucursal_id)
                DO UPDATE SET
                    stock_fisico   = inventario.stock_fisico + EXCLUDED.stock_fisico,
                    actualizado_en = now()
                RETURNING stock_fisico
                """,
                _uuid(empresa_id),
                vid,
                _uuid(destino_id),
                cant,
            )
            sf_destino_nuevo = int(dest_row["stock_fisico"])
            sf_destino_antes = sf_destino_nuevo - cant

            # 9. Movimientos kárdex
            await registrar_movimiento(
                conn,
                empresa_id=empresa_id,
                variante_id=vid_str,
                sucursal_id=origen_id,
                tipo="transferencia_salida",
                cantidad=-cant,
                stock_anterior=sf_antes,
                stock_nuevo=sf_origen_nuevo,
                usuario_id=user_id,
                motivo=motivo or "Transferencia entre sucursales",
                referencia_tipo="transferencia",
                referencia_id=str(transferencia_id),
            )

            await registrar_movimiento(
                conn,
                empresa_id=empresa_id,
                variante_id=vid_str,
                sucursal_id=destino_id,
                tipo="transferencia_entrada",
                cantidad=cant,
                stock_anterior=sf_destino_antes,
                stock_nuevo=sf_destino_nuevo,
                usuario_id=user_id,
                motivo=motivo or "Transferencia entre sucursales",
                referencia_tipo="transferencia",
                referencia_id=str(transferencia_id),
            )

    # --- 10. Auditoría (fuera de la tx) ---
    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="transferencia_inventario",
        entidad_id=str(transferencia_id),
        datos_despues={
            "origen_id": origen_id,
            "destino_id": destino_id,
            "motivo": motivo,
            "items": [
                {"variante_id": str(_uuid(it["variante_id"])), "cantidad": int(it["cantidad"])}
                for it in items
            ],
        },
    )

    return {
        "mensaje": "Transferencia realizada correctamente",
        "transferencia_id": str(transferencia_id),
        "origen_id": origen_id,
        "destino_id": destino_id,
        "estado": "recibida",
        "items_count": len(items),
    }


async def actualizar_parametros(
    empresa_id: str,
    user_id: str,
    inventario_id: str,
    stock_minimo: int | None = None,
    ubicacion: str | None = None,
) -> dict:
    """
    Actualiza stock_minimo y/o ubicacion de un registro de inventario.
    """
    if stock_minimo is None and ubicacion is None:
        raise api_error(422, "SIN_CAMBIOS", "Debe proporcionar al menos un campo a actualizar")

    if stock_minimo is not None and stock_minimo < 0:
        raise api_error(422, "STOCK_MINIMO_INVALIDO", "El stock mínimo no puede ser negativo")

    async with tenant_connection(empresa_id, user_id) as conn:
        inv = await conn.fetchrow(
            """
            SELECT id, variante_id, sucursal_id, stock_minimo, ubicacion
              FROM inventario
             WHERE id = $1 AND empresa_id = $2
            """,
            _uuid(inventario_id),
            _uuid(empresa_id),
        )
        if inv is None:
            raise api_error(404, "INVENTARIO_NO_ENCONTRADO", "El registro de inventario no existe")

        datos_antes = {
            "stock_minimo": inv["stock_minimo"],
            "ubicacion": inv["ubicacion"],
        }

        new_stock_min = stock_minimo if stock_minimo is not None else inv["stock_minimo"]
        new_ubicacion = ubicacion.strip() if ubicacion is not None else inv["ubicacion"]

        row = await conn.fetchrow(
            """
            UPDATE inventario
               SET stock_minimo   = $1,
                   ubicacion      = $2,
                   actualizado_en = now()
             WHERE id = $3 AND empresa_id = $4
            RETURNING id, variante_id, sucursal_id, stock_fisico, stock_reservado,
                      stock_disponible, stock_minimo, ubicacion, actualizado_en
            """,
            new_stock_min,
            new_ubicacion,
            _uuid(inventario_id),
            _uuid(empresa_id),
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="inventario",
        entidad_id=inventario_id,
        datos_antes=datos_antes,
        datos_despues={"stock_minimo": new_stock_min, "ubicacion": new_ubicacion},
    )

    return dict(row)


async def listar_movimientos(
    empresa_id: str,
    user_id: str,
    sucursal_id: str | None = None,
    variante_id: str | None = None,
    tipo: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Listado paginado del kárdex (movimiento_inventario).
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        conditions: list[str] = ["m.empresa_id = $1"]
        params: list[object] = [_uuid(empresa_id)]

        if sucursal_id:
            params.append(_uuid(sucursal_id))
            conditions.append(f"m.sucursal_id = ${len(params)}")

        if variante_id:
            params.append(_uuid(variante_id))
            conditions.append(f"m.variante_id = ${len(params)}")

        if tipo:
            params.append(tipo)
            conditions.append(f"m.tipo = ${len(params)}")

        if desde:
            params.append(desde)
            conditions.append(f"m.ocurrido_en >= ${len(params)}::timestamptz")

        if hasta:
            params.append(hasta)
            conditions.append(f"m.ocurrido_en <= ${len(params)}::timestamptz")

        where = " AND ".join(conditions)

        total: int = await conn.fetchval(
            f"SELECT count(*)::integer FROM movimiento_inventario m WHERE {where}",
            *params,
        )

        limit  = page_size
        offset = (page - 1) * page_size
        params.extend([limit, offset])

        rows = await conn.fetch(
            f"""
            SELECT m.id,
                   m.empresa_id,
                   m.variante_id,
                   m.sucursal_id,
                   s.nombre          AS sucursal_nombre,
                   m.tipo,
                   m.cantidad,
                   m.stock_anterior,
                   m.stock_nuevo,
                   m.referencia_tipo,
                   m.referencia_id,
                   m.motivo,
                   m.usuario_id,
                   m.ocurrido_en,
                   v.sku,
                   p.nombre          AS prenda_nombre
              FROM movimiento_inventario m
              JOIN sucursal s ON s.id = m.sucursal_id
              JOIN variante v ON v.id = m.variante_id
              JOIN prenda p   ON p.id = v.prenda_id
             WHERE {where}
             ORDER BY m.ocurrido_en DESC
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-total // page_size)),
            "items": [dict(r) for r in rows],
        }


async def get_disponibilidad_prenda(
    empresa_id: str,
    user_id: str,
    prenda_id: str,
) -> dict:
    """
    Disponibilidad de una prenda por sucursal, talla y color.
    Single JOIN query tal como especificado en CU-17.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        # Verificar que la prenda existe
        prenda = await conn.fetchrow(
            "SELECT id, codigo, nombre FROM prenda WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            _uuid(prenda_id),
            _uuid(empresa_id),
        )
        if prenda is None:
            raise api_error(404, "PRENDA_NO_ENCONTRADA", "La prenda no existe en el catálogo")

        rows = await conn.fetch(
            """
            SELECT s.id          AS sucursal_id,
                   s.nombre,
                   s.direccion,
                   ci.nombre     AS ciudad,
                   v.id          AS variante_id,
                   v.sku,
                   t.nombre      AS talla,
                   c.nombre      AS color,
                   i.stock_disponible,
                   i.actualizado_en
              FROM inventario i
              JOIN variante v  ON v.id = i.variante_id AND v.empresa_id = i.empresa_id
              JOIN prenda p    ON p.id = v.prenda_id
              JOIN sucursal s  ON s.id = i.sucursal_id AND s.empresa_id = i.empresa_id
              JOIN ciudad ci   ON ci.id = s.ciudad_id
              JOIN talla t     ON t.id = v.talla_id
              JOIN color c     ON c.id = v.color_id
             WHERE i.empresa_id = $1
               AND p.id         = $2
               AND s.estado     = 'activa'
               AND v.deleted_at IS NULL
             ORDER BY s.nombre, t.orden, c.nombre
            """,
            _uuid(empresa_id),
            _uuid(prenda_id),
        )

        sucursales: dict[str, dict] = {}
        for r in rows:
            sid = str(r["sucursal_id"])
            if sid not in sucursales:
                sucursales[sid] = {
                    "sucursal_id": r["sucursal_id"],
                    "nombre": r["nombre"],
                    "direccion": r["direccion"] or "",
                    "ciudad": r["ciudad"] or "",
                    "variantes": [],
                }
            sucursales[sid]["variantes"].append({
                "variante_id": r["variante_id"],
                "sku": r["sku"],
                "talla": r["talla"],
                "color": r["color"],
                "stock_disponible": r["stock_disponible"],
            })

        actualizado_en = (
            max(r["actualizado_en"] for r in rows)
            if rows
            else datetime.now(timezone.utc)
        )

        return {
            "prenda_id": prenda["id"],
            "agotado_en_todas": all(int(r["stock_disponible"]) <= 0 for r in rows),
            "actualizado_en": actualizado_en,
            "sucursales": list(sucursales.values()),
        }


class InventarioService:
    def __init__(self, pool=None):
        self.pool = pool

    async def listar_existencias(self, empresa_id: str, sucursal_id: str = None, solo_bajo_minimo: bool = False):
        return await listar_inventario(empresa_id=empresa_id, sucursal_id=sucursal_id, bajo_minimo=solo_bajo_minimo)

    async def registrar_ajuste(self, empresa_id: str, usuario_id: str, datos=None):
        return await registrar_ajuste(empresa_id=empresa_id, user_id=usuario_id, datos=datos)

    async def consultar_disponibilidad_variante(self, empresa_id: str, variante_id: str):
        return await get_disponibilidad_prenda(empresa_id=empresa_id, prenda_id=variante_id)
