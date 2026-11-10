"""
Servicio de Reservas – FashionStore
CU-19 Crear/Validar reserva
CU-20 Gestión encargado (preparar, incidencia)
CU-21 Cancelar / expirar reservas
"""

import logging
import random
import string
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection, get_pool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
VENTANA_GRACIA_HORAS = 2          # expira_en = fecha_visita + 2 h
MAX_LINEAS_RESERVA = 10
MAX_UNIDADES_RESERVA = 20
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin ambiguos (no 0,O,1,I)


# ---------------------------------------------------------------------------
# Helper: generador de código
# ---------------------------------------------------------------------------
def _generar_codigo() -> str:
    """Genera código de 6 chars del alfabeto sin ambiguos."""
    return "RSV-" + "".join(random.choices(ALFABETO_CODIGO, k=6))


# ---------------------------------------------------------------------------
# Helper: serializar fila asyncpg → dict
# ---------------------------------------------------------------------------
def _row(r) -> dict:
    return dict(r) if r else {}


def _rows(rs) -> list[dict]:
    return [dict(r) for r in rs]


# ---------------------------------------------------------------------------
# CU-19 – Validar reserva (sin efectos secundarios)
# ---------------------------------------------------------------------------
async def validar_reserva(
    empresa_id: str,
    user_id: str | None,
    sucursal_id: str,
    fecha_visita: datetime,
    items: list[dict],
) -> dict:
    """
    Verifica sin modificar nada:
      1. Sucursal activa del tenant
      2. fecha_visita en el futuro
      3. stock_disponible >= cantidad para cada variante en esa sucursal
    Retorna {"ok": True} o lanza 409 con detalle de faltantes.
    """
    ahora = datetime.now(timezone.utc)

    # 1. fecha_visita futura
    fv = fecha_visita if fecha_visita.tzinfo else fecha_visita.replace(tzinfo=timezone.utc)
    if fv <= ahora:
        raise api_error(422, "FECHA_INVALIDA", "La fecha_visita debe ser futura")

    async with tenant_connection(empresa_id, user_id) as conn:
        # 2. Sucursal activa del tenant
        sucursal = await conn.fetchrow(
            """
            SELECT id, nombre, estado
              FROM sucursal
             WHERE id = $1 AND empresa_id = $2
            """,
            UUID(sucursal_id),
            UUID(empresa_id),
        )
        if not sucursal:
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal no existe")
        if sucursal["estado"] != "activa":
            raise api_error(409, "SUCURSAL_INACTIVA", "La sucursal no está activa")

        # 3. Verificar stock por variante
        variante_ids = [UUID(str(it["variante_id"])) for it in items]
        inv_rows = await conn.fetch(
            """
            SELECT variante_id, stock_disponible
              FROM inventario
             WHERE empresa_id = $1
               AND sucursal_id = $2
               AND variante_id = ANY($3)
            """,
            UUID(empresa_id),
            UUID(sucursal_id),
            variante_ids,
        )
        inv_map = {str(r["variante_id"]): r["stock_disponible"] for r in inv_rows}

        faltantes = []
        for it in items:
            vid = str(it["variante_id"])
            disponible = inv_map.get(vid, 0)
            if disponible < it["cantidad"]:
                faltantes.append(
                    {
                        "variante_id": vid,
                        "solicitado": it["cantidad"],
                        "disponible": disponible,
                    }
                )

        if faltantes:
            raise api_error(
                409,
                "STOCK_INSUFICIENTE",
                "Stock insuficiente para uno o más ítems",
            )

    return {"ok": True}


# ---------------------------------------------------------------------------
# CU-19 – Crear reserva
# ---------------------------------------------------------------------------
async def crear_reserva(
    empresa_id: str,
    user_id: str,
    sucursal_id: str,
    fecha_visita: str | datetime,
    items: list[dict],
    cliente_uuid: str | None = None,
    ip: str | None = None,
) -> dict:
    """
    Crea una nueva reserva con bloqueo pesimista de inventario.
    Idempotente: si existe una reserva activa con el mismo cliente_uuid,
    la retorna sin crear una nueva.
    """
    ahora = datetime.now(timezone.utc)

    # Parsear fecha
    if isinstance(fecha_visita, str):
        try:
            fecha_visita = datetime.fromisoformat(fecha_visita)
        except ValueError:
            raise api_error(422, "FECHA_INVALIDA", "Formato de fecha_visita inválido")

    if fecha_visita.tzinfo is None:
        fecha_visita = fecha_visita.replace(tzinfo=timezone.utc)

    if fecha_visita <= ahora:
        raise api_error(422, "FECHA_INVALIDA", "La fecha_visita debe ser futura")

    # Validar límites
    if len(items) > MAX_LINEAS_RESERVA:
        raise api_error(
            422,
            "MAX_LINEAS_EXCEDIDO",
            f"Una reserva no puede tener más de {MAX_LINEAS_RESERVA} líneas",
        )

    total_unidades = sum(it["cantidad"] for it in items)
    if total_unidades > MAX_UNIDADES_RESERVA:
        raise api_error(
            422,
            "MAX_UNIDADES_EXCEDIDO",
            f"Una reserva no puede superar {MAX_UNIDADES_RESERVA} unidades en total",
        )

    # Consolidar cantidades por variante_id
    consolidado: dict[str, int] = {}
    for it in items:
        vid = str(it["variante_id"])
        consolidado[vid] = consolidado.get(vid, 0) + it["cantidad"]

    variante_ids = [UUID(v) for v in sorted(consolidado.keys())]  # orden determinista

    # Idempotencia por cliente_uuid
    if cliente_uuid:
        async with tenant_connection(empresa_id, user_id) as conn_check:
            existing = await conn_check.fetchrow(
                """
                SELECT id FROM reserva
                 WHERE empresa_id = $1
                   AND cliente_uuid = $2
                   AND estado NOT IN ('cancelada', 'expirada', 'convertida')
                """,
                UUID(empresa_id),
                UUID(cliente_uuid),
            )
            if existing:
                return await _get_reserva_completa(conn_check, empresa_id, str(existing["id"]))

    expira_en = fecha_visita + timedelta(hours=VENTANA_GRACIA_HORAS)

    async with tenant_connection(empresa_id, user_id) as conn:
        # -- Verificar sucursal activa
        sucursal = await conn.fetchrow(
            "SELECT id FROM sucursal WHERE id = $1 AND empresa_id = $2 AND estado = 'activa'",
            UUID(sucursal_id),
            UUID(empresa_id),
        )
        if not sucursal:
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "Sucursal no encontrada o inactiva")

        # a. Bloqueo pesimista de inventario
        inv_rows = await conn.fetch(
            """
            SELECT id, variante_id, stock_disponible, stock_reservado
              FROM inventario
             WHERE empresa_id = $1
               AND sucursal_id = $2
               AND variante_id = ANY($3)
             ORDER BY variante_id
             FOR UPDATE
            """,
            UUID(empresa_id),
            UUID(sucursal_id),
            variante_ids,
        )
        inv_map = {str(r["variante_id"]): r for r in inv_rows}

        # b. Verificar stock suficiente
        faltantes = []
        for vid, cantidad in consolidado.items():
            fila = inv_map.get(vid)
            disponible = fila["stock_disponible"] if fila else 0
            if disponible < cantidad:
                faltantes.append(
                    {"variante_id": vid, "solicitado": cantidad, "disponible": disponible}
                )

        if faltantes:
            raise api_error(409, "STOCK_INSUFICIENTE", "Stock insuficiente para uno o más ítems")

        # c. Actualizar stock_reservado
        for vid, cantidad in consolidado.items():
            await conn.execute(
                """
                UPDATE inventario
                   SET stock_reservado = stock_reservado + $1,
                       actualizado_en  = now()
                 WHERE empresa_id  = $2
                   AND sucursal_id = $3
                   AND variante_id = $4
                """,
                cantidad,
                UUID(empresa_id),
                UUID(sucursal_id),
                UUID(vid),
            )

        # d. Generar código único (hasta 5 intentos)
        codigo = None
        for _ in range(5):
            candidato = _generar_codigo()
            existe = await conn.fetchval(
                "SELECT id FROM reserva WHERE empresa_id = $1 AND codigo = $2",
                UUID(empresa_id),
                candidato,
            )
            if not existe:
                codigo = candidato
                break

        if codigo is None:
            raise api_error(500, "CODIGO_COLISION", "No se pudo generar un código único")

        # e. Insertar reserva
        reserva_row = await conn.fetchrow(
            """
            INSERT INTO reserva
                (empresa_id, usuario_id, sucursal_id, estado, codigo,
                 fecha_visita, expira_en, cliente_uuid)
            VALUES ($1, $2, $3, 'pendiente_preparacion', $4, $5, $6, $7)
            RETURNING *
            """,
            UUID(empresa_id),
            UUID(user_id),
            UUID(sucursal_id),
            codigo,
            fecha_visita,
            expira_en,
            UUID(cliente_uuid) if cliente_uuid else None,
        )
        reserva_id = reserva_row["id"]

        # f. Insertar detalles
        for vid, cantidad in consolidado.items():
            await conn.execute(
                """
                INSERT INTO reserva_detalle (empresa_id, reserva_id, variante_id, cantidad)
                VALUES ($1, $2, $3, $4)
                """,
                UUID(empresa_id),
                reserva_id,
                UUID(vid),
                cantidad,
            )

        # g. Historial de estado
        await conn.execute(
            """
            INSERT INTO reserva_estado_historial
                (empresa_id, reserva_id, estado_anterior, estado_nuevo, motivo, usuario_id)
            VALUES ($1, $2, NULL, 'pendiente_preparacion', 'Creación de reserva', $3)
            """,
            UUID(empresa_id),
            reserva_id,
            UUID(user_id),
        )

        reserva_dict = _row(reserva_row)
        resultado = await _get_reserva_completa(conn, empresa_id, str(reserva_id))

    # Auditoría (fuera de la transacción)
    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="reserva",
        entidad_id=str(reserva_id),
        datos_despues={
            "codigo": codigo,
            "sucursal_id": sucursal_id,
            "fecha_visita": str(fecha_visita),
            "items": [{"variante_id": k, "cantidad": v} for k, v in consolidado.items()],
        },
        ip=ip,
    )

    return resultado


# ---------------------------------------------------------------------------
# CU-19/20/21 – Listar reservas (paginado, filtrado por rol)
# ---------------------------------------------------------------------------
async def listar_reservas(
    empresa_id: str,
    user_id: str,
    rol: str,
    sucursal_id_usuario: str | None = None,
    estado: str | None = None,
    sucursal_id_filtro: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Retorna lista paginada de reservas según el rol del usuario:
    - cliente: solo sus propias reservas
    - encargado: solo reservas de su sucursal
    - administrador/superadmin: todas del tenant
    """
    offset = (page - 1) * page_size

    async with tenant_connection(empresa_id, user_id) as conn:
        conditions = ["r.empresa_id = $1"]
        params: list = [UUID(empresa_id)]

        # Filtro por rol
        if rol == "cliente":
            params.append(UUID(user_id))
            conditions.append(f"r.usuario_id = ${len(params)}")
        elif rol == "encargado":
            if sucursal_id_usuario:
                params.append(UUID(sucursal_id_usuario))
                conditions.append(f"r.sucursal_id = ${len(params)}")

        # Filtros opcionales
        if estado:
            params.append(estado)
            conditions.append(f"r.estado = ${len(params)}")

        if sucursal_id_filtro and rol not in ("cliente", "encargado"):
            params.append(UUID(sucursal_id_filtro))
            conditions.append(f"r.sucursal_id = ${len(params)}")

        if desde:
            fv_desde = desde if desde.tzinfo else desde.replace(tzinfo=timezone.utc)
            params.append(fv_desde)
            conditions.append(f"r.fecha_visita >= ${len(params)}")

        if hasta:
            fv_hasta = hasta if hasta.tzinfo else hasta.replace(tzinfo=timezone.utc)
            params.append(fv_hasta)
            conditions.append(f"r.fecha_visita <= ${len(params)}")

        where = " AND ".join(conditions)

        total = await conn.fetchval(
            f"SELECT count(*)::int FROM reserva r WHERE {where}", *params
        )

        params.extend([page_size, offset])
        rows = await conn.fetch(
            f"""
            SELECT r.*,
                   s.nombre AS sucursal_nombre
              FROM reserva r
              LEFT JOIN sucursal s ON s.id = r.sucursal_id
             WHERE {where}
             ORDER BY r.fecha_visita DESC
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

        items = []
        for r in rows:
            det = await _get_detalles_reserva(conn, empresa_id, str(r["id"]))
            items.append({**_row(r), "items": det, "historial": None})

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


# ---------------------------------------------------------------------------
# CU-19/20/21 – Obtener reserva por ID (con historial)
# ---------------------------------------------------------------------------
async def get_reserva(
    empresa_id: str,
    user_id: str,
    rol: str,
    reserva_id: str,
    sucursal_id_usuario: str | None = None,
) -> dict:
    """Retorna la reserva completa con historial. Respeta aislamiento por rol."""
    async with tenant_connection(empresa_id, user_id) as conn:
        r = await conn.fetchrow(
            "SELECT * FROM reserva WHERE id = $1 AND empresa_id = $2",
            UUID(reserva_id),
            UUID(empresa_id),
        )
        if not r:
            raise api_error(404, "RESERVA_NO_ENCONTRADA", "Reserva no encontrada")

        # Aislamiento por rol
        if rol == "cliente" and str(r["usuario_id"]) != user_id:
            raise api_error(403, "ACCESO_DENEGADO", "No tienes acceso a esta reserva")
        if rol == "encargado" and sucursal_id_usuario and str(r["sucursal_id"]) != sucursal_id_usuario:
            raise api_error(403, "ACCESO_DENEGADO", "Esta reserva no pertenece a tu sucursal")

        sucursal = await conn.fetchrow(
            "SELECT nombre FROM sucursal WHERE id = $1", r["sucursal_id"]
        )

        det = await _get_detalles_reserva(conn, empresa_id, reserva_id)
        historial = await _get_historial_reserva(conn, empresa_id, reserva_id)

        return {
            **_row(r),
            "sucursal_nombre": sucursal["nombre"] if sucursal else None,
            "items": det,
            "historial": historial,
        }


# ---------------------------------------------------------------------------
# CU-21 – Cancelar reserva
# ---------------------------------------------------------------------------
async def cancelar_reserva(
    empresa_id: str,
    user_id: str,
    rol: str,
    reserva_id: str,
    motivo: str | None = None,
    ip: str | None = None,
) -> dict:
    """
    Cancela una reserva en estado 'pendiente_preparacion'.
    Idempotente: si ya está cancelada retorna el estado actual.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        # a. Bloqueo pesimista de la reserva
        r = await conn.fetchrow(
            "SELECT * FROM reserva WHERE id = $1 AND empresa_id = $2 FOR UPDATE",
            UUID(reserva_id),
            UUID(empresa_id),
        )
        if not r:
            raise api_error(404, "RESERVA_NO_ENCONTRADA", "Reserva no encontrada")

        # Aislamiento por rol
        if rol == "cliente" and str(r["usuario_id"]) != user_id:
            raise api_error(403, "ACCESO_DENEGADO", "No tienes acceso a esta reserva")

        estado_actual = r["estado"]

        # Idempotencia
        if estado_actual == "cancelada":
            det = await _get_detalles_reserva(conn, empresa_id, reserva_id)
            historial = await _get_historial_reserva(conn, empresa_id, reserva_id)
            return {**_row(r), "items": det, "historial": historial}

        # Solo cancelable desde 'pendiente_preparacion'
        if estado_actual != "pendiente_preparacion":
            raise api_error(
                409,
                "ESTADO_INVALIDO",
                f"No es posible anular reservas en estado {estado_actual}",
            )

        # Obtener detalles para liberar stock
        detalles = await conn.fetch(
            "SELECT variante_id, cantidad FROM reserva_detalle WHERE reserva_id = $1 AND empresa_id = $2",
            UUID(reserva_id),
            UUID(empresa_id),
        )
        variante_ids = [d["variante_id"] for d in detalles]

        # b. Bloqueo de inventario (orden determinista)
        await conn.fetch(
            """
            SELECT id FROM inventario
             WHERE empresa_id = $1 AND sucursal_id = $2 AND variante_id = ANY($3)
             ORDER BY variante_id
             FOR UPDATE
            """,
            UUID(empresa_id),
            r["sucursal_id"],
            variante_ids,
        )

        # c. Liberar stock_reservado
        for d in detalles:
            await conn.execute(
                """
                UPDATE inventario
                   SET stock_reservado = GREATEST(0, stock_reservado - $1),
                       actualizado_en  = now()
                 WHERE empresa_id  = $2
                   AND sucursal_id = $3
                   AND variante_id = $4
                """,
                d["cantidad"],
                UUID(empresa_id),
                r["sucursal_id"],
                d["variante_id"],
            )

        # d. Actualizar estado de reserva
        reserva_updated = await conn.fetchrow(
            """
            UPDATE reserva
               SET estado      = 'cancelada',
                   updated_at  = now()
             WHERE id = $1
            RETURNING *
            """,
            UUID(reserva_id),
        )

        # e. Historial
        await conn.execute(
            """
            INSERT INTO reserva_estado_historial
                (empresa_id, reserva_id, estado_anterior, estado_nuevo, motivo, usuario_id)
            VALUES ($1, $2, $3, 'cancelada', $4, $5)
            """,
            UUID(empresa_id),
            UUID(reserva_id),
            estado_actual,
            motivo or "Cancelada por usuario",
            UUID(user_id),
        )

        det = await _get_detalles_reserva(conn, empresa_id, reserva_id)
        historial = await _get_historial_reserva(conn, empresa_id, reserva_id)
        resultado = {**_row(reserva_updated), "items": det, "historial": historial}

    logger.info("NOTIFICACION: Reserva %s cancelada por usuario %s", r["codigo"], user_id)

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="reserva",
        entidad_id=reserva_id,
        datos_antes={"estado": estado_actual},
        datos_despues={"estado": "cancelada", "motivo": motivo},
        ip=ip,
    )

    return resultado


# ---------------------------------------------------------------------------
# CU-21 – Expirar reservas vencidas (tarea de fondo / cron)
# ---------------------------------------------------------------------------
async def expirar_reservas_vencidas(empresa_id: str | None = None) -> int:
    """
    Busca reservas 'pendiente_preparacion' cuyo expira_en < now() y las marca
    como 'expiradas' liberando stock. Si empresa_id es None, procesa todos los tenants.
    Retorna el total de reservas expiradas.
    """
    pool = get_pool()
    total_expiradas = 0
    ahora = datetime.now(timezone.utc)

    async with pool.acquire() as conn:
        # Obtener empresas a procesar
        if empresa_id:
            empresas = [empresa_id]
        else:
            rows = await conn.fetch(
                "SELECT DISTINCT empresa_id FROM reserva WHERE estado = 'pendiente_preparacion' AND expira_en < $1",
                ahora,
            )
            empresas = [str(r["empresa_id"]) for r in rows]

    for eid in empresas:
        try:
            async with tenant_connection(eid, None) as conn:
                # Obtener reservas vencidas con bloqueo
                vencidas = await conn.fetch(
                    """
                    SELECT r.id, r.sucursal_id, r.codigo
                      FROM reserva r
                     WHERE r.empresa_id = $1
                       AND r.estado     = 'pendiente_preparacion'
                       AND r.expira_en  < $2
                     FOR UPDATE SKIP LOCKED
                    """,
                    UUID(eid),
                    ahora,
                )

                for rv in vencidas:
                    reserva_id = rv["id"]

                    # Detalles para liberar stock
                    detalles = await conn.fetch(
                        "SELECT variante_id, cantidad FROM reserva_detalle WHERE reserva_id = $1 AND empresa_id = $2",
                        reserva_id,
                        UUID(eid),
                    )

                    # Liberar stock_reservado
                    for d in detalles:
                        await conn.execute(
                            """
                            UPDATE inventario
                               SET stock_reservado = GREATEST(0, stock_reservado - $1),
                                   actualizado_en  = now()
                             WHERE empresa_id  = $2
                               AND sucursal_id = $3
                               AND variante_id = $4
                            """,
                            d["cantidad"],
                            UUID(eid),
                            rv["sucursal_id"],
                            d["variante_id"],
                        )

                    # Marcar como expirada
                    await conn.execute(
                        """
                        UPDATE reserva
                           SET estado     = 'expirada',
                               updated_at = now()
                         WHERE id = $1
                        """,
                        reserva_id,
                    )

                    # Historial
                    await conn.execute(
                        """
                        INSERT INTO reserva_estado_historial
                            (empresa_id, reserva_id, estado_anterior, estado_nuevo, motivo, usuario_id)
                        VALUES ($1, $2, 'pendiente_preparacion', 'expirada', 'Expiración automática', NULL)
                        """,
                        UUID(eid),
                        reserva_id,
                    )

                    logger.info(
                        "Reserva %s [empresa=%s] expirada automáticamente", rv["codigo"], eid
                    )
                    total_expiradas += 1

        except Exception as exc:
            logger.error("Error al expirar reservas de empresa %s: %s", eid, exc)

    return total_expiradas


# ---------------------------------------------------------------------------
# CU-20 – Listar reservas por preparar (encargado)
# ---------------------------------------------------------------------------
async def listar_por_preparar(
    empresa_id: str,
    user_id: str,
    sucursal_id_encargado: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Reservas 'pendiente_preparacion' de la sucursal del encargado, por fecha_visita ASC."""
    offset = (page - 1) * page_size

    async with tenant_connection(empresa_id, user_id) as conn:
        if not sucursal_id_encargado:
            sucursal_id_encargado = await conn.fetchval(
                "SELECT sucursal_id FROM usuario WHERE id = $1 AND empresa_id = $2",
                UUID(user_id),
                UUID(empresa_id),
            )

        conditions = ["r.empresa_id = $1", "r.estado = 'pendiente_preparacion'"]
        params: list = [UUID(empresa_id)]
        if sucursal_id_encargado:
            params.append(UUID(str(sucursal_id_encargado)))
            conditions.append(f"r.sucursal_id = ${len(params)}")
        where = " AND ".join(conditions)

        total = await conn.fetchval(
            f"SELECT count(*)::int FROM reserva r WHERE {where}",
            *params,
        )

        params.extend([page_size, offset])
        rows = await conn.fetch(
            f"""
            SELECT r.*,
                   s.nombre AS sucursal_nombre
              FROM reserva r
              LEFT JOIN sucursal s ON s.id = r.sucursal_id
             WHERE {where}
             ORDER BY r.fecha_visita ASC
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

        items = []
        for r in rows:
            det = await _get_detalles_reserva(conn, empresa_id, str(r["id"]))
            items.append({**_row(r), "items": det, "historial": None})

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


# ---------------------------------------------------------------------------
# CU-20 – Preparar reserva (encargado)
# ---------------------------------------------------------------------------
async def preparar_reserva(
    empresa_id: str,
    user_id: str,
    reserva_id: str,
    probador: str | None = None,
    ip: str | None = None,
) -> dict:
    """
    Encargado marca la reserva como 'preparada' asignando probador.
    Verifica que la reserva pertenece a su sucursal, no esté vencida
    y esté en 'pendiente_preparacion'.
    """
    ahora = datetime.now(timezone.utc)

    async with tenant_connection(empresa_id, user_id) as conn:
        # Obtener datos del encargado (sucursal)
        encargado = await conn.fetchrow(
            "SELECT sucursal_id FROM usuario WHERE id = $1 AND empresa_id = $2",
            UUID(user_id),
            UUID(empresa_id),
        )
        sucursal_id_encargado = encargado["sucursal_id"] if encargado else None

        r = await conn.fetchrow(
            "SELECT * FROM reserva WHERE id = $1 AND empresa_id = $2 FOR UPDATE",
            UUID(reserva_id),
            UUID(empresa_id),
        )
        if not r:
            raise api_error(404, "RESERVA_NO_ENCONTRADA", "Reserva no encontrada")

        # Verificar que pertenece a la sucursal del encargado
        if sucursal_id_encargado and str(r["sucursal_id"]) != str(sucursal_id_encargado):
            raise api_error(403, "ACCESO_DENEGADO", "Esta reserva no pertenece a tu sucursal")

        if r["estado"] != "pendiente_preparacion":
            raise api_error(
                409,
                "ESTADO_INVALIDO",
                f"Solo se pueden preparar reservas en 'pendiente_preparacion'. Estado actual: {r['estado']}",
            )

        # Verificar que no esté vencida
        expira_en = r["expira_en"]
        if expira_en.tzinfo is None:
            expira_en = expira_en.replace(tzinfo=timezone.utc)
        if expira_en <= ahora:
            raise api_error(409, "RESERVA_VENCIDA", "La reserva ya venció")

        # Actualizar estado
        reserva_updated = await conn.fetchrow(
            """
            UPDATE reserva
               SET estado     = 'preparada',
                   probador   = $1,
                   updated_at = now()
             WHERE id = $2
            RETURNING *
            """,
            probador,
            UUID(reserva_id),
        )

        # Historial
        await conn.execute(
            """
            INSERT INTO reserva_estado_historial
                (empresa_id, reserva_id, estado_anterior, estado_nuevo, motivo, usuario_id)
            VALUES ($1, $2, 'pendiente_preparacion', 'preparada', 'Preparada por encargado', $3)
            """,
            UUID(empresa_id),
            UUID(reserva_id),
            UUID(user_id),
        )

        det = await _get_detalles_reserva(conn, empresa_id, reserva_id)
        historial = await _get_historial_reserva(conn, empresa_id, reserva_id)
        resultado = {**_row(reserva_updated), "items": det, "historial": historial}

    # Notificación al cliente
    logger.info(
        "NOTIFICACION: Reserva %s lista en probador %s",
        r["codigo"],
        probador or "sin asignar",
    )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="reserva",
        entidad_id=reserva_id,
        datos_antes={"estado": "pendiente_preparacion"},
        datos_despues={"estado": "preparada", "probador": probador},
        ip=ip,
    )

    return resultado


# ---------------------------------------------------------------------------
# CU-21 – Completar reserva tras atención / prueba en tienda
# ---------------------------------------------------------------------------
async def completar_reserva(
    empresa_id: str,
    user_id: str,
    reserva_id: str,
    motivo: str | None = None,
    ip: str | None = None,
) -> dict:
    """
    Marca la reserva como 'completada', libera el stock reservado en inventario
    si no había sido liberado aún, registra el historial de estados y audita.
    """
    motivo_final = (motivo or "Reserva completada en sucursal").strip()

    async with tenant_connection(empresa_id, user_id) as conn:
        encargado = await conn.fetchrow(
            "SELECT sucursal_id FROM usuario WHERE id = $1 AND empresa_id = $2",
            UUID(user_id),
            UUID(empresa_id),
        )
        sucursal_id_encargado = encargado["sucursal_id"] if encargado else None

        r = await conn.fetchrow(
            "SELECT * FROM reserva WHERE id = $1 AND empresa_id = $2 FOR UPDATE",
            UUID(reserva_id),
            UUID(empresa_id),
        )
        if not r:
            raise api_error(404, "RESERVA_NO_ENCONTRADA", "Reserva no encontrada")

        if sucursal_id_encargado and str(r["sucursal_id"]) != str(sucursal_id_encargado):
            raise api_error(403, "ACCESO_DENEGADO", "Esta reserva no pertenece a tu sucursal")

        estado_anterior = r["estado"]
        if estado_anterior not in ("pendiente_preparacion", "preparada", "activa", "confirmada"):
            raise api_error(
                409,
                "ESTADO_INVALIDO",
                f"No es posible completar una reserva en estado '{estado_anterior}'",
            )

        if r["liberada_en"] is None and estado_anterior in ("pendiente_preparacion", "preparada"):
            detalles = await conn.fetch(
                "SELECT variante_id, cantidad FROM reserva_detalle WHERE reserva_id = $1 AND empresa_id = $2",
                UUID(reserva_id),
                UUID(empresa_id),
            )
            variante_ids = [d["variante_id"] for d in detalles]
            if variante_ids:
                await conn.fetch(
                    """
                    SELECT id FROM inventario
                     WHERE empresa_id = $1 AND sucursal_id = $2 AND variante_id = ANY($3)
                     ORDER BY variante_id
                     FOR UPDATE
                    """,
                    UUID(empresa_id),
                    r["sucursal_id"],
                    variante_ids,
                )
                for d in detalles:
                    await conn.execute(
                        """
                        UPDATE inventario
                           SET stock_reservado = GREATEST(0, stock_reservado - $1),
                               actualizado_en  = now()
                         WHERE empresa_id  = $2
                           AND sucursal_id = $3
                           AND variante_id = $4
                        """,
                        d["cantidad"],
                        UUID(empresa_id),
                        r["sucursal_id"],
                        d["variante_id"],
                    )

        reserva_updated = await conn.fetchrow(
            """
            UPDATE reserva
               SET estado        = 'completada',
                   liberada_en   = COALESCE(liberada_en, now()),
                   motivo_cierre = $1,
                   updated_at    = now()
             WHERE id = $2
               AND empresa_id = $3
            RETURNING *
            """,
            motivo_final[:200],
            UUID(reserva_id),
            UUID(empresa_id),
        )

        # Garantizar historial único si el trigger ya insertó o en DB simulada sin triggers
        ya_en_historial = await conn.fetchval(
            """
            SELECT 1
              FROM reserva_estado_historial
             WHERE reserva_id = $1
               AND empresa_id = $2
               AND estado_nuevo = 'completada'
               AND ocurrido_en >= now() - interval '5 seconds'
             LIMIT 1
            """,
            UUID(reserva_id),
            UUID(empresa_id),
        )
        if not ya_en_historial:
            await conn.execute(
                """
                INSERT INTO reserva_estado_historial
                    (empresa_id, reserva_id, estado_anterior, estado_nuevo, motivo, usuario_id)
                VALUES ($1, $2, $3, 'completada', $4, $5)
                """,
                UUID(empresa_id),
                UUID(reserva_id),
                estado_anterior,
                motivo_final[:200],
                UUID(user_id),
            )

        resultado = await _get_reserva_completa(conn, empresa_id, reserva_id)

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="reserva",
        entidad_id=reserva_id,
        datos_antes={"estado": estado_anterior},
        datos_despues={"estado": "completada", "motivo": motivo_final},
        ip=ip,
    )

    return resultado


# ---------------------------------------------------------------------------
# CU-20 – Reportar incidencia de stock (encargado)
# ---------------------------------------------------------------------------
async def reportar_incidencia(
    empresa_id: str,
    user_id: str,
    reserva_id: str,
    variante_ids: list[str],
    motivo: str,
    registrar_merma: bool = False,
    ip: str | None = None,
) -> dict:
    """
    Marca la reserva como 'incidencia_stock'. Opcionalmente registra merma
    ajustando stock_fisico y stock_reservado de las variantes afectadas.
    Busca alternativas disponibles (misma prenda, otras variantes o sucursales).
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        # Obtener sucursal del encargado
        encargado = await conn.fetchrow(
            "SELECT sucursal_id FROM usuario WHERE id = $1 AND empresa_id = $2",
            UUID(user_id),
            UUID(empresa_id),
        )
        sucursal_id_encargado = encargado["sucursal_id"] if encargado else None

        r = await conn.fetchrow(
            "SELECT * FROM reserva WHERE id = $1 AND empresa_id = $2 FOR UPDATE",
            UUID(reserva_id),
            UUID(empresa_id),
        )
        if not r:
            raise api_error(404, "RESERVA_NO_ENCONTRADA", "Reserva no encontrada")

        # Verificar sucursal del encargado
        if sucursal_id_encargado and str(r["sucursal_id"]) != str(sucursal_id_encargado):
            raise api_error(403, "ACCESO_DENEGADO", "Esta reserva no pertenece a tu sucursal")

        # Estado válido para reportar incidencia
        if r["estado"] not in ("pendiente_preparacion", "preparada"):
            raise api_error(
                409,
                "ESTADO_INVALIDO",
                f"No se puede reportar incidencia en reserva con estado '{r['estado']}'",
            )

        estado_anterior = r["estado"]

        # 2. Actualizar estado de la reserva
        await conn.execute(
            """
            UPDATE reserva
               SET estado     = 'incidencia_stock',
                   updated_at = now()
             WHERE id = $1
            """,
            UUID(reserva_id),
        )

        # 3. Historial
        await conn.execute(
            """
            INSERT INTO reserva_estado_historial
                (empresa_id, reserva_id, estado_anterior, estado_nuevo, motivo, usuario_id)
            VALUES ($1, $2, $3, 'incidencia_stock', $4, $5)
            """,
            UUID(empresa_id),
            UUID(reserva_id),
            estado_anterior,
            motivo,
            UUID(user_id),
        )

        # 4. Registrar merma si se solicita
        if registrar_merma and variante_ids:
            # Obtener cantidades de los detalles de la reserva
            detalles_afectados = await conn.fetch(
                """
                SELECT variante_id, cantidad
                  FROM reserva_detalle
                 WHERE reserva_id = $1
                   AND empresa_id = $2
                   AND variante_id = ANY($3)
                """,
                UUID(reserva_id),
                UUID(empresa_id),
                [UUID(v) for v in variante_ids],
            )

            for d in detalles_afectados:
                await conn.execute(
                    """
                    UPDATE inventario
                       SET stock_fisico    = GREATEST(0, stock_fisico    - $1),
                           stock_reservado = GREATEST(0, stock_reservado - $1),
                           actualizado_en  = now()
                     WHERE empresa_id  = $2
                       AND sucursal_id = $3
                       AND variante_id = $4
                    """,
                    d["cantidad"],
                    UUID(empresa_id),
                    r["sucursal_id"],
                    d["variante_id"],
                )

        # 5. Buscar alternativas (misma prenda, otras variantes/sucursales con stock > 0)
        alternativas = []
        if variante_ids:
            # Obtener prenda_ids de las variantes afectadas
            prendas = await conn.fetch(
                "SELECT DISTINCT prenda_id FROM variante WHERE id = ANY($1) AND empresa_id = $2",
                [UUID(v) for v in variante_ids],
                UUID(empresa_id),
            )
            prenda_ids = [p["prenda_id"] for p in prendas]

            if prenda_ids:
                alt_rows = await conn.fetch(
                    """
                    SELECT v.id        AS variante_id,
                           v.sku,
                           p.nombre   AS prenda_nombre,
                           t.nombre   AS talla,
                           c.nombre   AS color,
                           i.sucursal_id,
                           s.nombre   AS sucursal_nombre,
                           i.stock_disponible
                      FROM variante v
                      JOIN prenda   p ON p.id = v.prenda_id
                      JOIN talla    t ON t.id = v.talla_id
                      JOIN color    c ON c.id = v.color_id
                      JOIN inventario i ON i.variante_id = v.id AND i.empresa_id = $1
                      JOIN sucursal  s ON s.id = i.sucursal_id
                     WHERE v.empresa_id  = $1
                       AND v.prenda_id   = ANY($2)
                       AND v.id         != ALL($3)
                       AND v.deleted_at IS NULL
                       AND i.stock_disponible > 0
                       AND s.estado = 'activa'
                     ORDER BY i.stock_disponible DESC
                     LIMIT 20
                    """,
                    UUID(empresa_id),
                    prenda_ids,
                    [UUID(v) for v in variante_ids],
                )
                alternativas = _rows(alt_rows)

        reserva_updated = await conn.fetchrow(
            "SELECT * FROM reserva WHERE id = $1", UUID(reserva_id)
        )
        det = await _get_detalles_reserva(conn, empresa_id, reserva_id)
        historial = await _get_historial_reserva(conn, empresa_id, reserva_id)

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="reserva",
        entidad_id=reserva_id,
        datos_antes={"estado": estado_anterior},
        datos_despues={
            "estado": "incidencia_stock",
            "motivo": motivo,
            "variantes_afectadas": variante_ids,
            "registrar_merma": registrar_merma,
        },
        ip=ip,
    )

    return {
        "reserva_id": str(reserva_id),
        "estado": "incidencia_stock",
        "reserva": {**_row(reserva_updated), "items": det, "historial": historial},
        "alternativas": alternativas,
    }


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
async def _get_reserva_completa(conn, empresa_id: str, reserva_id: str) -> dict:
    """Carga reserva + detalles + historial usando una conexión existente."""
    r = await conn.fetchrow(
        """
        SELECT r.*, s.nombre AS sucursal_nombre
          FROM reserva r
          LEFT JOIN sucursal s ON s.id = r.sucursal_id
         WHERE r.id = $1 AND r.empresa_id = $2
        """,
        UUID(reserva_id),
        UUID(empresa_id),
    )
    if not r:
        raise api_error(404, "RESERVA_NO_ENCONTRADA", "Reserva no encontrada")

    det = await _get_detalles_reserva(conn, empresa_id, reserva_id)
    historial = await _get_historial_reserva(conn, empresa_id, reserva_id)

    return {**_row(r), "items": det, "historial": historial}


async def _get_detalles_reserva(conn, empresa_id: str, reserva_id: str) -> list[dict]:
    """Retorna los ítems de la reserva con info de variante/prenda."""
    rows = await conn.fetch(
        """
        SELECT rd.variante_id,
               v.sku,
               p.nombre        AS prenda_nombre,
               t.nombre        AS talla,
               c.nombre        AS color,
               rd.cantidad,
               i.ubicacion
          FROM reserva_detalle rd
          JOIN variante  v ON v.id = rd.variante_id
          JOIN prenda    p ON p.id = v.prenda_id
          JOIN talla     t ON t.id = v.talla_id
          JOIN color     c ON c.id = v.color_id
          LEFT JOIN inventario i
                 ON i.variante_id = rd.variante_id
                AND i.empresa_id  = rd.empresa_id
                AND i.sucursal_id = (
                    SELECT sucursal_id FROM reserva WHERE id = rd.reserva_id
                )
         WHERE rd.reserva_id = $1
           AND rd.empresa_id = $2
         ORDER BY p.nombre, t.nombre
        """,
        UUID(reserva_id),
        UUID(empresa_id),
    )
    return _rows(rows)


async def _get_historial_reserva(conn, empresa_id: str, reserva_id: str) -> list[dict]:
    """Retorna el historial de estados de la reserva."""
    rows = await conn.fetch(
        """
        SELECT estado_anterior, estado_nuevo, motivo, usuario_id, ocurrido_en
          FROM reserva_estado_historial
         WHERE reserva_id = $1 AND empresa_id = $2
         ORDER BY ocurrido_en ASC
        """,
        UUID(reserva_id),
        UUID(empresa_id),
    )
    return _rows(rows)


class ReservaService:
    def __init__(self, pool=None):
        self.pool = pool

    async def crear_reserva(self, empresa_id: str, cliente_id: str, datos=None):
        sucursal_id = str(getattr(datos, "sucursal_id", "") or (datos.get("sucursal_id") if isinstance(datos, dict) else ""))
        fecha_visita = getattr(datos, "fecha_visita", None) or (datos.get("fecha_visita") if isinstance(datos, dict) else None)
        raw_items = getattr(datos, "items", None) or (datos.get("items") if isinstance(datos, dict) else [])
        items = [it.model_dump() if hasattr(it, "model_dump") else it for it in raw_items]
        return await crear_reserva(
            empresa_id=empresa_id,
            user_id=cliente_id,
            sucursal_id=sucursal_id,
            fecha_visita=fecha_visita,
            items=items,
        )

    async def mis_reservas(self, empresa_id: str, cliente_id: str, estado: str | None = None):
        return await listar_reservas(
            empresa_id=empresa_id,
            user_id=cliente_id,
            rol="cliente",
            estado=estado,
        )

    async def cancelar_reserva(self, empresa_id: str, reserva_id: str, cliente_id: str, motivo: str | None = None):
        return await cancelar_reserva(
            empresa_id=empresa_id,
            user_id=cliente_id,
            rol="cliente",
            reserva_id=reserva_id,
            motivo=motivo,
        )

    async def listar_reservas(
        self,
        empresa_id: str,
        sucursal_id: str | None = None,
        estado: str | None = None,
        usuario_id: str | None = None,
        rol: str = "administrador",
    ):
        return await listar_reservas(
            empresa_id=empresa_id,
            user_id=usuario_id or empresa_id,
            rol=rol,
            sucursal_id_filtro=sucursal_id,
            estado=estado,
        )

    async def preparar_reserva(self, empresa_id: str, reserva_id: str, usuario_id: str, probador: str | None = None):
        return await preparar_reserva(
            empresa_id=empresa_id,
            user_id=usuario_id,
            reserva_id=reserva_id,
            probador=probador,
        )

    async def completar_reserva(self, empresa_id: str, reserva_id: str, usuario_id: str, motivo: str | None = None):
        return await completar_reserva(
            empresa_id=empresa_id,
            user_id=usuario_id,
            reserva_id=reserva_id,
            motivo=motivo,
        )

    async def registrar_incidencia(
        self,
        empresa_id: str,
        reserva_id: str,
        usuario_id: str,
        detalle: str,
        variante_ids: list[str] | None = None,
        registrar_merma: bool = False,
    ):
        return await reportar_incidencia(
            empresa_id=empresa_id,
            user_id=usuario_id,
            reserva_id=reserva_id,
            variante_ids=variante_ids or [],
            motivo=detalle,
            registrar_merma=registrar_merma,
        )
