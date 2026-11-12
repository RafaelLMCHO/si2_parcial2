"""
Servicio de Checkout / Creación de Órdenes (CU-23).
Gestiona la validación de checkout, creación de venta y finalización de pago.
"""
import hashlib
import hmac
import logging
import os
import secrets
from decimal import Decimal
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
TASA_IVA = Decimal("0.13")          # 13 % IVA configurable
COSTO_ENVIO_DEFAULT = Decimal("20.00")  # Costo de envío por defecto (configurable)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _generar_firma_qr(empresa_id: str, numero: str, total: Decimal, fecha: str, nonce: str) -> str:
    """HMAC-SHA256 sobre empresa_id|numero|total|fecha|nonce."""
    secret = os.environ.get("QR_FIRMA_SECRET", "fashionstore-secret-key")
    msg = f"{empresa_id}|{numero}|{total}|{fecha}|{nonce}"
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


async def _get_carrito_activo(conn, empresa_id: str, user_id: str) -> tuple[str, list[dict]]:
    """Retorna (carrito_id, items) del carrito activo. Lanza error si vacío."""
    carrito_id = await conn.fetchval(
        "SELECT id FROM carrito WHERE empresa_id=$1 AND usuario_id=$2 AND estado='activo' LIMIT 1",
        UUID(empresa_id), UUID(user_id),
    )
    if carrito_id is None:
        raise api_error(400, "CARRITO_VACIO", "No hay carrito activo para este usuario")

    items = await conn.fetch(
        """
        SELECT cd.id, cd.variante_id, cd.cantidad, cd.precio_unitario,
               v.precio_venta AS precio_lista
          FROM carrito_detalle cd
          JOIN variante v ON v.id = cd.variante_id
         WHERE cd.carrito_id = $1 AND cd.empresa_id = $2
        """,
        carrito_id, UUID(empresa_id),
    )
    if not items:
        raise api_error(400, "CARRITO_VACIO", "El carrito no tiene ítems")

    return str(carrito_id), [dict(r) for r in items]


async def _buscar_sucursal_despacho(conn, empresa_id: str, items: list[dict]) -> tuple[str | None, str | None]:
    """
    Busca la sucursal de despacho con suficiente stock.
    1. Intenta con la sucursal matriz (es_matriz=true).
    2. Si no tiene stock suficiente, busca la activa con mayor stock de los ítems.
    Retorna (sucursal_id, sucursal_nombre) o (None, None).
    """
    variante_ids = [UUID(str(i["variante_id"])) for i in items]
    cantidades = {str(i["variante_id"]): i["cantidad"] for i in items}

    # Buscar sucursal matriz
    matriz = await conn.fetchrow(
        """
        SELECT id, nombre FROM sucursal
         WHERE empresa_id=$1 AND es_matriz=true AND estado='activa' AND deleted_at IS NULL
         LIMIT 1
        """,
        UUID(empresa_id),
    )

    async def tiene_stock(sucursal_id: UUID) -> bool:
        for variante_id, cantidad in cantidades.items():
            stock = await conn.fetchval(
                """
                SELECT COALESCE(stock_disponible, 0) FROM inventario
                 WHERE empresa_id=$1 AND sucursal_id=$2 AND variante_id=$3
                """,
                UUID(empresa_id), sucursal_id, UUID(variante_id),
            )
            if (stock or 0) < cantidad:
                return False
        return True

    if matriz and await tiene_stock(matriz["id"]):
        return str(matriz["id"]), matriz["nombre"]

    # Si la matriz no tiene stock, buscar la activa con mayor stock total
    sucursales = await conn.fetch(
        """
        SELECT s.id, s.nombre,
               COALESCE(SUM(inv.stock_disponible), 0) AS stock_total
          FROM sucursal s
          LEFT JOIN inventario inv
                  ON inv.sucursal_id = s.id
                AND inv.empresa_id = s.empresa_id
                AND inv.variante_id = ANY($2::uuid[])
         WHERE s.empresa_id = $1 AND s.estado = 'activa' AND s.deleted_at IS NULL
         GROUP BY s.id, s.nombre
         ORDER BY stock_total DESC
        """,
        UUID(empresa_id), variante_ids,
    )

    for suc in sucursales:
        if await tiene_stock(suc["id"]):
            return str(suc["id"]), suc["nombre"]

    return None, None


async def _verificar_stock(conn, empresa_id: str, sucursal_id: str, items: list[dict]) -> list[dict]:
    """
    Verifica stock en la sucursal de despacho.
    Retorna lista de líneas faltantes [{variante_id, disponible, solicitado}].
    """
    lineas_faltantes = []
    for item in items:
        stock = await conn.fetchval(
            """
            SELECT COALESCE(stock_disponible, 0) FROM inventario
             WHERE empresa_id=$1 AND sucursal_id=$2 AND variante_id=$3
            """,
            UUID(empresa_id), UUID(sucursal_id), UUID(str(item["variante_id"])),
        )
        disponible = int(stock or 0)
        if disponible < item["cantidad"]:
            lineas_faltantes.append({
                "variante_id": str(item["variante_id"]),
                "disponible": disponible,
                "solicitado": item["cantidad"],
            })
    return lineas_faltantes


async def _validar_cupon(
    conn,
    empresa_id: str,
    user_id: str,
    cupon_codigo: str,
    subtotal: Decimal,
) -> tuple[str | None, Decimal]:
    """
    Valida el cupón y calcula el descuento.
    Retorna (cupon_id, descuento_aplicado).
    """
    cupon = await conn.fetchrow(
        """
        SELECT id, tipo, valor, monto_minimo, usos_maximos, usos_por_usuario, fecha_inicio, fecha_fin
          FROM cupon
         WHERE empresa_id=$1 AND lower(codigo)=lower($2) AND activo=true
         LIMIT 1
        """,
        UUID(empresa_id), cupon_codigo,
    )
    if cupon is None:
        raise api_error(404, "CUPON_NO_ENCONTRADO", f"El cupón '{cupon_codigo}' no existe o está inactivo")

    # Validar monto mínimo
    if cupon["monto_minimo"] and subtotal < cupon["monto_minimo"]:
        raise api_error(
            422, "CUPON_MONTO_MINIMO",
            f"El subtotal debe ser al menos {cupon['monto_minimo']} para usar este cupón",
        )

    # Validar fechas
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if cupon["fecha_inicio"] and now < cupon["fecha_inicio"].replace(tzinfo=timezone.utc):
        raise api_error(422, "CUPON_NO_VIGENTE", "El cupón aún no está vigente")
    if cupon["fecha_fin"] and now > cupon["fecha_fin"].replace(tzinfo=timezone.utc):
        raise api_error(422, "CUPON_EXPIRADO", "El cupón ha expirado")

    # Validar usos totales
    if cupon["usos_maximos"] is not None:
        usos = await conn.fetchval(
            "SELECT COUNT(*) FROM cupon_uso WHERE empresa_id=$1 AND cupon_id=$2",
            UUID(empresa_id), cupon["id"],
        )
        if int(usos) >= cupon["usos_maximos"]:
            raise api_error(422, "CUPON_AGOTADO", "El cupón ha alcanzado su límite de usos")

    # Validar usos por usuario
    if cupon["usos_por_usuario"] is not None:
        usos_user = await conn.fetchval(
            "SELECT COUNT(*) FROM cupon_uso WHERE empresa_id=$1 AND cupon_id=$2 AND usuario_id=$3",
            UUID(empresa_id), cupon["id"], UUID(user_id),
        )
        if int(usos_user) >= cupon["usos_por_usuario"]:
            raise api_error(422, "CUPON_LIMITE_USUARIO", "Ya usaste este cupón el máximo de veces permitido")

    # Calcular descuento
    if cupon["tipo"] == "porcentaje":
        descuento = (subtotal * Decimal(str(cupon["valor"])) / Decimal("100")).quantize(Decimal("0.01"))
    else:  # monto_fijo
        descuento = min(Decimal(str(cupon["valor"])), subtotal)

    return str(cupon["id"]), descuento


# ---------------------------------------------------------------------------
# Endpoints públicos
# ---------------------------------------------------------------------------

async def listar_direcciones_cliente(empresa_id: str, user_id: str) -> list[dict]:
    """Lista las direcciones activas del cliente dentro del tenant actual."""
    async with tenant_connection(empresa_id, user_id) as conn:
        rows = await conn.fetch(
            """
            SELECT d.id,
                   d.etiqueta,
                   d.destinatario,
                   d.telefono,
                   d.linea1,
                   d.linea2,
                   c.nombre AS ciudad,
                   c.departamento,
                   d.referencia,
                   d.es_principal
              FROM direccion_cliente d
              JOIN ciudad c ON c.id = d.ciudad_id
             WHERE d.empresa_id = $1
               AND d.usuario_id = $2
               AND d.deleted_at IS NULL
             ORDER BY d.es_principal DESC, d.created_at ASC
            """,
            UUID(empresa_id),
            UUID(user_id),
        )
        return [dict(r) for r in rows]


async def validar_checkout(
    empresa_id: str,
    user_id: str,
    tipo_entrega: str,
    direccion_id: str = None,
    sucursal_id: str = None,
    cupon_codigo: str = None,
) -> dict:
    """
    Verifica stock, calcula totales, valida cupón.
    Sin efectos secundarios (solo lectura).
    Retorna dict con subtotal, descuento, impuesto, costo_envio, total_a_pagar,
    sucursal_despacho_id, sucursal_despacho_nombre, cupon_id, lineas_faltantes.
    """
    if tipo_entrega == "envio" and not direccion_id:
        raise api_error(422, "DIRECCION_REQUERIDA", "Debe indicar una dirección para envío")
    if tipo_entrega == "recojo" and not sucursal_id:
        raise api_error(422, "SUCURSAL_REQUERIDA", "Debe indicar una sucursal para recojo")

    async with tenant_connection(empresa_id, user_id) as conn:
        _, items = await _get_carrito_activo(conn, empresa_id, user_id)

        # Determinar sucursal de despacho
        if tipo_entrega == "recojo":
            suc = await conn.fetchrow(
                "SELECT id, nombre FROM sucursal WHERE id=$1 AND empresa_id=$2 AND deleted_at IS NULL",
                UUID(sucursal_id), UUID(empresa_id),
            )
            if suc is None:
                raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal seleccionada no existe")
            despacho_id = str(suc["id"])
            despacho_nombre = suc["nombre"]
        else:
            dir_row = await conn.fetchrow(
                """
                SELECT id FROM direccion_cliente
                 WHERE id=$1 AND empresa_id=$2 AND usuario_id=$3 AND deleted_at IS NULL
                """,
                UUID(direccion_id), UUID(empresa_id), UUID(user_id),
            )
            if dir_row is None:
                raise api_error(404, "DIRECCION_NO_ENCONTRADA", "La dirección de envío seleccionada no existe")
            despacho_id, despacho_nombre = await _buscar_sucursal_despacho(conn, empresa_id, items)

        lineas_faltantes = []
        if despacho_id:
            lineas_faltantes = await _verificar_stock(conn, empresa_id, despacho_id, items)

        # Calcular subtotal
        subtotal = sum(
            Decimal(str(i["precio_unitario"])) * i["cantidad"]
            for i in items
        ).quantize(Decimal("0.01"))

        # Validar y aplicar cupón
        descuento = Decimal("0.00")
        cupon_id = None
        if cupon_codigo:
            cupon_id, descuento = await _validar_cupon(conn, empresa_id, user_id, cupon_codigo, subtotal)

        # Costo de envío
        costo_envio = COSTO_ENVIO_DEFAULT if tipo_entrega == "envio" else Decimal("0.00")

        # Impuesto sobre (subtotal - descuento + costo_envio)
        base_imponible = subtotal - descuento + costo_envio
        impuesto = (base_imponible * TASA_IVA).quantize(Decimal("0.01"))
        total_a_pagar = (base_imponible + impuesto).quantize(Decimal("0.01"))

        return {
            "subtotal": subtotal,
            "descuento": descuento,
            "impuesto": impuesto,
            "costo_envio": costo_envio,
            "total_a_pagar": total_a_pagar,
            "sucursal_despacho_id": UUID(despacho_id) if despacho_id else None,
            "sucursal_despacho_nombre": despacho_nombre,
            "cupon_id": UUID(cupon_id) if cupon_id else None,
            "lineas_faltantes": lineas_faltantes,
        }


async def crear_orden(
    empresa_id: str,
    user_id: str,
    idempotency_key: str,
    tipo_entrega: str,
    direccion_id: str = None,
    sucursal_id: str = None,
    cupon_codigo: str = None,
    ip: str = None,
) -> dict:
    """
    Crea venta en estado 'pendiente_pago' (canal='WEB').
    NO descuenta stock todavía.
    Idempotente: si ya existe una venta con idempotency_key, retorna esa.
    """
    if tipo_entrega == "envio" and not direccion_id:
        raise api_error(422, "DIRECCION_REQUERIDA", "Debe indicar una dirección para envío")
    if tipo_entrega == "recojo" and not sucursal_id:
        raise api_error(422, "SUCURSAL_REQUERIDA", "Debe indicar una sucursal para recojo")

    async with tenant_connection(empresa_id, user_id) as conn:
        # Idempotencia: verificar si ya existe venta con esta key
        existente = await conn.fetchrow(
            """
            SELECT id, numero, total, estado FROM venta
             WHERE empresa_id=$1 AND idempotency_key=$2
            """,
            UUID(empresa_id), idempotency_key,
        )
        if existente is not None:
            logger.info("Orden ya existente por idempotency_key=%s", idempotency_key)
            return {
                "venta_id": existente["id"],
                "numero": existente["numero"],
                "total_a_pagar": existente["total"],
                "estado": existente["estado"],
            }

        carrito_id, items = await _get_carrito_activo(conn, empresa_id, user_id)

        # Determinar sucursal de despacho
        if tipo_entrega == "recojo":
            suc = await conn.fetchrow(
                "SELECT id, nombre FROM sucursal WHERE id=$1 AND empresa_id=$2 AND deleted_at IS NULL",
                UUID(sucursal_id), UUID(empresa_id),
            )
            if suc is None:
                raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal seleccionada no existe")
            despacho_id = str(suc["id"])
        else:
            dir_row = await conn.fetchrow(
                """
                SELECT id FROM direccion_cliente
                 WHERE id=$1 AND empresa_id=$2 AND usuario_id=$3 AND deleted_at IS NULL
                """,
                UUID(direccion_id), UUID(empresa_id), UUID(user_id),
            )
            if dir_row is None:
                raise api_error(404, "DIRECCION_NO_ENCONTRADA", "La dirección de envío seleccionada no existe")
            despacho_id, _ = await _buscar_sucursal_despacho(conn, empresa_id, items)

        # Calcular totales
        subtotal = sum(
            Decimal(str(i["precio_unitario"])) * i["cantidad"]
            for i in items
        ).quantize(Decimal("0.01"))

        descuento = Decimal("0.00")
        cupon_id = None
        if cupon_codigo:
            cupon_id, descuento = await _validar_cupon(conn, empresa_id, user_id, cupon_codigo, subtotal)

        costo_envio = COSTO_ENVIO_DEFAULT if tipo_entrega == "envio" else Decimal("0.00")
        base_imponible = subtotal - descuento + costo_envio
        impuesto = (base_imponible * TASA_IVA).quantize(Decimal("0.01"))
        total = (base_imponible + impuesto).quantize(Decimal("0.01"))

        # Número correlativo seguro: V-00001
        n = await conn.fetchval(
            "SELECT COUNT(*)::int + 1 FROM venta WHERE empresa_id=$1",
            UUID(empresa_id),
        )
        numero = f"V-{int(n):05d}"

        # Firma QR
        from datetime import datetime, timezone
        fecha_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        nonce = secrets.token_hex(16)
        firma_qr = _generar_firma_qr(empresa_id, numero, total, fecha_str, nonce)

        # Insertar venta
        venta_id = await conn.fetchval(
            """
            INSERT INTO venta (
                empresa_id, numero, usuario_id, canal,
                subtotal, descuento, impuesto, total,
                estado, idempotency_key,
                firma_qr, qr_nonce, firma_algoritmo,
                cupon_id, sucursal_id, direccion_id
            )
            VALUES ($1,$2,$3,'WEB',$4,$5,$6,$7,'pendiente_pago',$8,$9,$10,'HMAC-SHA256',$11,$12,$13)
            RETURNING id
            """,
            UUID(empresa_id), numero, UUID(user_id),
            subtotal, descuento, impuesto, total,
            idempotency_key, firma_qr, nonce,
            UUID(cupon_id) if cupon_id else None,
            UUID(despacho_id) if despacho_id else None,
            UUID(direccion_id) if direccion_id else None,
        )

        # Insertar historial de estado
        await conn.execute(
            """
            INSERT INTO venta_estado_historial
                (empresa_id, venta_id, estado_anterior, estado_nuevo, motivo, usuario_id)
            VALUES ($1,$2,NULL,'pendiente_pago','Creación de orden',$3)
            """,
            UUID(empresa_id), venta_id, UUID(user_id),
        )

        # Insertar venta_detalle
        for item in items:
            precio_lista = Decimal(str(item.get("precio_lista") or item["precio_unitario"]))
            precio_unitario = Decimal(str(item["precio_unitario"]))
            cantidad = item["cantidad"]
            descuento_linea = Decimal("0.00")
            subtotal_linea = (precio_unitario * cantidad - descuento_linea).quantize(Decimal("0.01"))

            await conn.execute(
                """
                INSERT INTO venta_detalle (
                    empresa_id, venta_id, variante_id, cantidad,
                    precio_lista, precio_unitario, descuento_linea, subtotal
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                UUID(empresa_id), venta_id, UUID(str(item["variante_id"])),
                cantidad, precio_lista, precio_unitario, descuento_linea, subtotal_linea,
            )

        # Crear registro de envío solo para entregas a domicilio.
        # El recojo no genera fila en envio porque direccion_id es obligatorio.
        if tipo_entrega == "envio":
            await conn.execute(
                """
                INSERT INTO envio (empresa_id, venta_id, direccion_id, costo, estado)
                VALUES ($1,$2,$3,$4,'pendiente')
                """,
                UUID(empresa_id), venta_id,
                UUID(direccion_id) if direccion_id else None,
                costo_envio,
            )

        result = {
            "venta_id": venta_id,
            "numero": numero,
            "total_a_pagar": total,
            "estado": "pendiente_pago",
        }

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="venta",
        entidad_id=str(venta_id),
        datos_despues={
            "numero": numero,
            "total": str(total),
            "tipo_entrega": tipo_entrega,
            "canal": "WEB",
        },
        ip=ip,
    )
    return result


async def finalizar_venta_pagada(
    empresa_id: str,
    venta_id: str,
    pago_id: str = None,
    ip: str = None,
) -> None:
    """
    Idempotente: si venta ya es 'completada', no hace nada.
    En UNA transacción:
    1. Cargar venta y bloquear inventario (FOR UPDATE ORDER BY variante_id)
    2. Re-verificar stock; si no alcanza → venta='anulada' + reembolso (log)
    3. Descontar stock_fisico en sucursal de despacho
    4. INSERT movimiento_inventario tipo='venta' por cada línea
    5. venta → 'pagada' → 'completada' + historial
    6. cupon_uso si hubo cupón
    7. carrito → 'convertido'
    8. Auditoría
    """
    async with tenant_connection(empresa_id) as conn:
        venta = await conn.fetchrow(
            """
            SELECT id, numero, estado, sucursal_id, usuario_id, cajero_id, cupon_id, total
              FROM venta
             WHERE id=$1 AND empresa_id=$2
            """,
            UUID(venta_id), UUID(empresa_id),
        )
        if venta is None:
            raise api_error(404, "VENTA_NO_ENCONTRADA", "La venta no existe")

        # Idempotente
        if venta["estado"] == "completada":
            logger.info("Venta %s ya está completada, omitiendo", venta_id)
            return

        if venta["estado"] not in ("pendiente_pago", "pagada", "pago_fallido"):
            raise api_error(
                422, "ESTADO_INVALIDO",
                f"La venta está en estado '{venta['estado']}' y no se puede completar",
            )

        actor_usuario_id = venta["usuario_id"] or venta["cajero_id"]

        # Cargar líneas de detalle
        lineas = await conn.fetch(
            """
            SELECT vd.id, vd.variante_id, vd.cantidad
              FROM venta_detalle vd
             WHERE vd.venta_id=$1 AND vd.empresa_id=$2
             ORDER BY vd.variante_id
            """,
            UUID(venta_id), UUID(empresa_id),
        )

        sucursal_id = venta["sucursal_id"]

        # Bloquear inventario para evitar condición de carrera
        if sucursal_id:
            variante_ids = [r["variante_id"] for r in lineas]
            inv_rows = await conn.fetch(
                """
                SELECT variante_id, stock_fisico
                  FROM inventario
                 WHERE empresa_id=$1 AND sucursal_id=$2 AND variante_id=ANY($3::uuid[])
                 ORDER BY variante_id
                 FOR UPDATE
                """,
                UUID(empresa_id), sucursal_id, variante_ids,
            )
            inv_map = {str(r["variante_id"]): int(r["stock_fisico"]) for r in inv_rows}

            # Re-verificar stock
            sin_stock = [
                linea["variante_id"]
                for linea in lineas
                if inv_map.get(str(linea["variante_id"]), 0) < linea["cantidad"]
            ]

            if sin_stock:
                # El trigger de venta registra automáticamente el historial de estado.
                await conn.execute(
                    """
                    UPDATE venta
                       SET estado='anulada',
                           notas=COALESCE(notas, '') || ' | Stock insuficiente al confirmar pago',
                           updated_at=now()
                     WHERE id=$1
                    """,
                    UUID(venta_id),
                )
                logger.warning(
                    "Venta %s anulada por stock insuficiente. Variantes sin stock: %s. "
                    "Reembolso requerido para pago_id=%s",
                    venta_id, [str(v) for v in sin_stock], pago_id,
                )
                return

            # Descontar stock y registrar movimientos
            for linea in lineas:
                variante_id = linea["variante_id"]
                cantidad = int(linea["cantidad"])
                stock_anterior = inv_map[str(variante_id)]
                stock_nuevo = stock_anterior - cantidad

                await conn.execute(
                    """
                    UPDATE inventario
                       SET stock_fisico = stock_fisico - $1,
                           actualizado_en = now()
                     WHERE empresa_id=$2 AND sucursal_id=$3 AND variante_id=$4
                    """,
                    cantidad, UUID(empresa_id), sucursal_id, variante_id,
                )
                await conn.execute(
                    """
                    INSERT INTO movimiento_inventario (
                        empresa_id, sucursal_id, variante_id,
                        tipo, cantidad, stock_anterior, stock_nuevo,
                        referencia_id, referencia_tipo, usuario_id
                    )
                    VALUES ($1,$2,$3,'venta',$4,$5,$6,$7,'venta',$8)
                    """,
                    UUID(empresa_id), sucursal_id, variante_id,
                    -cantidad, stock_anterior, stock_nuevo,
                    UUID(venta_id), actor_usuario_id,
                )

        # Actualizar estado venta: pendiente_pago → pagada → completada.
        # fn_registrar_historial_venta inserta el historial automáticamente.
        await conn.execute(
            "UPDATE venta SET estado='pagada', updated_at=now() WHERE id=$1",
            UUID(venta_id),
        )
        await conn.execute(
            "UPDATE venta SET estado='completada', updated_at=now() WHERE id=$1",
            UUID(venta_id),
        )

        # Registrar uso de cupón
        if venta["cupon_id"] and venta["usuario_id"]:
            existing_uso = await conn.fetchval(
                "SELECT id FROM cupon_uso WHERE empresa_id=$1 AND cupon_id=$2 AND venta_id=$3",
                UUID(empresa_id), venta["cupon_id"], UUID(venta_id),
            )
            if existing_uso is None:
                await conn.execute(
                    """
                    INSERT INTO cupon_uso (empresa_id, cupon_id, usuario_id, venta_id)
                    VALUES ($1,$2,$3,$4)
                    """,
                    UUID(empresa_id), venta["cupon_id"], venta["usuario_id"],
                    UUID(venta_id),
                )

        # Marcar carrito como convertido
        if venta["usuario_id"]:
            await conn.execute(
                """
                UPDATE carrito SET estado='convertido', updated_at=now()
                 WHERE empresa_id=$1 AND usuario_id=$2 AND estado='activo'
                """,
                UUID(empresa_id), venta["usuario_id"],
            )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=str(actor_usuario_id) if actor_usuario_id else None,
        actor_tipo="sistema",
        accion="update",
        entidad="venta",
        entidad_id=venta_id,
        datos_despues={"estado": "completada", "pago_id": pago_id},
        ip=ip,
    )


async def reintentar_pago(
    empresa_id: str,
    user_id: str,
    venta_id: str,
) -> dict:
    """
    Para venta en 'pago_fallido', permite crear nueva intención de pago.
    Resetea el estado a 'pendiente_pago' y retorna los datos de la venta.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        venta = await conn.fetchrow(
            """
            SELECT id, numero, total, estado, usuario_id FROM venta
             WHERE id=$1 AND empresa_id=$2
            """,
            UUID(venta_id), UUID(empresa_id),
        )
        if venta is None:
            raise api_error(404, "VENTA_NO_ENCONTRADA", "La venta no existe")

        if str(venta["usuario_id"]) != user_id:
            raise api_error(403, "ACCESO_DENEGADO", "No tienes permiso sobre esta venta")

        if venta["estado"] != "pago_fallido":
            raise api_error(
                422, "ESTADO_INVALIDO",
                f"Solo se puede reintentar una venta en estado 'pago_fallido'. Estado actual: '{venta['estado']}'",
            )

        await conn.execute(
            "UPDATE venta SET estado='pendiente_pago', updated_at=now() WHERE id=$1",
            UUID(venta_id),
        )
        return {
            "venta_id": venta["id"],
            "numero": venta["numero"],
            "total_a_pagar": venta["total"],
            "estado": "pendiente_pago",
        }


async def get_comprobante_data(empresa_id: str, user_id: str, venta_id: str) -> dict:
    """
    Carga datos para PDF del comprobante.
    Verifica aislamiento tenant y que el usuario sea dueño (o staff).
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        venta = await conn.fetchrow(
            """
            SELECT v.id, v.numero, v.canal, v.estado,
                   v.subtotal, v.descuento, v.impuesto, v.total,
                   v.cliente_nombre, v.cliente_documento,
                   v.firma_qr, v.qr_nonce,
                   v.usuario_id,
                   v.created_at,
                   e.nombre AS empresa_nombre,
                   e.nit AS empresa_nit
              FROM venta v
              JOIN empresa e ON e.id = v.empresa_id
             WHERE v.id=$1 AND v.empresa_id=$2
            """,
            UUID(venta_id), UUID(empresa_id),
        )
        if venta is None:
            raise api_error(404, "VENTA_NO_ENCONTRADA", "El comprobante no existe")

        # Solo el propietario puede ver su comprobante (a menos que sea staff)
        if str(venta["usuario_id"]) != user_id:
            raise api_error(403, "ACCESO_DENEGADO", "No tienes permiso para ver este comprobante")

        lineas = await conn.fetch(
            """
            SELECT vd.variante_id,
                   p.nombre AS prenda_nombre,
                   v.sku,
                   ta.nombre AS talla,
                   co.nombre AS color,
                   vd.cantidad, vd.precio_lista, vd.precio_unitario,
                   vd.descuento_linea, vd.subtotal
              FROM venta_detalle vd
              JOIN variante v ON v.id = vd.variante_id
              JOIN prenda p ON p.id = v.prenda_id
              JOIN talla ta ON ta.id = v.talla_id
              JOIN color co ON co.id = v.color_id
             WHERE vd.venta_id=$1 AND vd.empresa_id=$2
             ORDER BY vd.id
            """,
            UUID(venta_id), UUID(empresa_id),
        )

        return {
            "venta_id": str(venta["id"]),
            "numero": venta["numero"],
            "canal": venta["canal"],
            "estado": venta["estado"],
            "empresa_nombre": venta["empresa_nombre"],
            "empresa_nit": venta["empresa_nit"],
            "subtotal": venta["subtotal"],
            "descuento": venta["descuento"],
            "impuesto": venta["impuesto"],
            "total": venta["total"],
            "cliente_nombre": venta["cliente_nombre"],
            "cliente_documento": venta["cliente_documento"],
            "firma_qr": venta["firma_qr"],
            "fecha_hora": venta["created_at"],
            "lineas": [
                {
                    "prenda_nombre": r["prenda_nombre"],
                    "sku": r["sku"],
                    "talla": r["talla"],
                    "color": r["color"],
                    "cantidad": r["cantidad"],
                    "precio_lista": r["precio_lista"],
                    "precio_unitario": r["precio_unitario"],
                    "descuento_linea": r["descuento_linea"],
                    "subtotal": r["subtotal"],
                }
                for r in lineas
            ],
        }


class CheckoutService:
    def __init__(self, pool=None):
        self.pool = pool

    async def crear_orden(self, empresa_id: str, cliente_id: str, datos=None):
        return await crear_orden(empresa_id=empresa_id, user_id=cliente_id, req=datos)
