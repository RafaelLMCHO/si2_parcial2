"""
Servicio de Punto de Venta POS Online (CU-23).
Gestiona venta directa en mostrador con escaneo de código de barras, facturación y cobro.
"""
import hashlib
import hmac
import logging
import os
import secrets
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection

logger = logging.getLogger(__name__)

TASA_IVA = Decimal("0.13")  # 13% IVA estándar


def _generar_firma_pos(empresa_id: str, numero: str, total: Decimal, fecha: str, nonce: str) -> str:
    secret = os.environ.get("QR_FIRMA_SECRET", "fashionstore-pos-secret")
    msg = f"{empresa_id}|{numero}|{total}|{fecha}|{nonce}"
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


async def _resolver_sucursal_cajero(
    conn, empresa_id: str, user_id: str, rol: str, sucursal_solicitada: Optional[str] = None
) -> str:
    """
    Determina la sucursal activa donde opera el cajero.
    Para Superadmin permite indicar sucursal_solicitada.
    Para Cajero/Encargado/Admin se obtiene de su perfil o se valida que pertenezca a la empresa.
    """
    if rol == "superadmin" and sucursal_solicitada:
        suc = await conn.fetchrow(
            "SELECT id, estado FROM sucursal WHERE id = $1 AND empresa_id = $2",
            UUID(sucursal_solicitada),
            UUID(empresa_id),
        )
        if not suc or suc["estado"] != "activa":
            raise api_error(404, "SUCURSAL_INVALIDA", "La sucursal indicada no está activa o no existe")
        return str(suc["id"])

    # Obtener sucursal asignada al usuario
    user_row = await conn.fetchrow(
        "SELECT sucursal_id FROM usuario WHERE id = $1 AND empresa_id = $2",
        UUID(user_id),
        UUID(empresa_id),
    )
    if not user_row or not user_row["sucursal_id"]:
        # Fallback para admin que no tiene sucursal_id fija: usar la matriz o la solicitada
        if sucursal_solicitada:
            suc = await conn.fetchrow(
                "SELECT id, estado FROM sucursal WHERE id = $1 AND empresa_id = $2",
                UUID(sucursal_solicitada),
                UUID(empresa_id),
            )
            if suc and suc["estado"] == "activa":
                return str(suc["id"])

        matriz = await conn.fetchval(
            "SELECT id FROM sucursal WHERE empresa_id = $1 AND es_matriz = true AND estado = 'activa' LIMIT 1",
            UUID(empresa_id),
        )
        if matriz:
            return str(matriz)
        raise api_error(403, "SIN_SUCURSAL_ASIGNADA", "El usuario no tiene una sucursal activa asignada para operar en caja")

    suc_id = user_row["sucursal_id"]
    suc_activa = await conn.fetchval(
        "SELECT id FROM sucursal WHERE id = $1 AND empresa_id = $2 AND estado = 'activa'",
        suc_id,
        UUID(empresa_id),
    )
    if not suc_activa:
        raise api_error(403, "SUCURSAL_INACTIVA", "La sucursal asignada al cajero no se encuentra activa")

    return str(suc_id)


async def _validar_dispositivo_pos(
    conn, empresa_id: str, sucursal_id: str, device_serial: Optional[str]
) -> Optional[str]:
    """Si se envía X-Device-Serial, verifica que el dispositivo pertenezca a la sucursal y esté activo."""
    if not device_serial:
        return None

    disp = await conn.fetchrow(
        """
        SELECT id, estado, sucursal_id
          FROM dispositivo
         WHERE empresa_id = $1 AND serial = $2
        """,
        UUID(empresa_id),
        device_serial.strip(),
    )
    if not disp:
        raise api_error(403, "DISPOSITIVO_NO_REGISTRADO", f"Dispositivo '{device_serial}' no reconocido en esta empresa")

    if disp["estado"] != "activo":
        raise api_error(403, "DISPOSITIVO_REVOCADO", "El terminal POS ha sido revocado o está inactivo")

    if str(disp["sucursal_id"]) != sucursal_id:
        raise api_error(403, "DISPOSITIVO_OTRA_SUCURSAL", "El terminal POS pertenece a una sucursal diferente")

    return str(disp["id"])


# ---------------------------------------------------------------------------
# Consultas de Artículos para POS
# ---------------------------------------------------------------------------

async def buscar_por_barcode(
    empresa_id: str, user_id: str, rol: str, codigo: str, sucursal_id_param: Optional[str] = None
) -> dict:
    """Busca una prenda/variante por código de barras o SKU en la sucursal del cajero."""
    async with tenant_connection(empresa_id, user_id) as conn:
        sucursal_id = await _resolver_sucursal_cajero(conn, empresa_id, user_id, rol, sucursal_id_param)

        row = await conn.fetchrow(
            """
            SELECT v.id AS variante_id,
                   v.sku,
                   v.codigo_barras,
                   v.precio_venta,
                   p.id AS prenda_id,
                   p.nombre AS prenda_nombre,
                   p.imagen_url,
                   t.nombre AS talla,
                   c.nombre AS color,
                   COALESCE(i.stock_disponible, 0) AS stock_disponible
              FROM variante v
              JOIN prenda p ON p.id = v.prenda_id
              JOIN talla t ON t.id = v.talla_id
              JOIN color c ON c.id = v.color_id
              LEFT JOIN inventario i
                     ON i.variante_id = v.id
                    AND i.sucursal_id = $1
                    AND i.empresa_id = $2
             WHERE (v.codigo_barras = $3 OR v.sku = $3)
               AND v.empresa_id = $2
               AND v.deleted_at IS NULL
               AND p.deleted_at IS NULL
            """,
            UUID(sucursal_id),
            UUID(empresa_id),
            codigo.strip(),
        )

        if not row:
            raise api_error(404, "ARTICULO_NO_ENCONTRADO", f"No se encontró ninguna variante con código '{codigo}'")

        return {
            "variante_id": str(row["variante_id"]),
            "sku": row["sku"],
            "codigo_barras": row["codigo_barras"],
            "prenda_nombre": row["prenda_nombre"],
            "imagen_url": row["imagen_url"],
            "talla": row["talla"],
            "color": row["color"],
            "precio_venta": row["precio_venta"],
            "stock_disponible": row["stock_disponible"],
            "sucursal_id": sucursal_id,
        }


async def buscar_variantes(
    empresa_id: str,
    user_id: str,
    rol: str,
    q: Optional[str] = None,
    sucursal_id_param: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Búsqueda textual paginada de variantes con stock en la sucursal del cajero."""
    async with tenant_connection(empresa_id, user_id) as conn:
        sucursal_id = await _resolver_sucursal_cajero(conn, empresa_id, user_id, rol, sucursal_id_param)

        offset = (page - 1) * page_size
        search_filter = f"%{q.strip().lower()}%" if q else "%"

        total = await conn.fetchval(
            """
            SELECT COUNT(*)
              FROM variante v
              JOIN prenda p ON p.id = v.prenda_id
             WHERE v.empresa_id = $1
               AND v.deleted_at IS NULL
               AND (lower(p.nombre) LIKE $2 OR lower(v.sku) LIKE $2 OR lower(COALESCE(v.codigo_barras, '')) LIKE $2)
            """,
            UUID(empresa_id),
            search_filter,
        )

        rows = await conn.fetch(
            """
            SELECT v.id AS variante_id,
                   v.sku,
                   v.codigo_barras,
                   v.precio_venta,
                   p.nombre AS prenda_nombre,
                   t.nombre AS talla,
                   c.nombre AS color,
                   COALESCE(i.stock_disponible, 0) AS stock_disponible
              FROM variante v
              JOIN prenda p ON p.id = v.prenda_id
              JOIN talla t ON t.id = v.talla_id
              JOIN color c ON c.id = v.color_id
              LEFT JOIN inventario i
                     ON i.variante_id = v.id
                    AND i.sucursal_id = $1
                    AND i.empresa_id = $2
             WHERE v.empresa_id = $2
               AND v.deleted_at IS NULL
               AND (lower(p.nombre) LIKE $3 OR lower(v.sku) LIKE $3 OR lower(COALESCE(v.codigo_barras, '')) LIKE $3)
             ORDER BY p.nombre, v.sku
             LIMIT $4 OFFSET $5
            """,
            UUID(sucursal_id),
            UUID(empresa_id),
            search_filter,
            page_size,
            offset,
        )

        items = [
            {
                "variante_id": str(r["variante_id"]),
                "sku": r["sku"],
                "codigo_barras": r["codigo_barras"],
                "prenda_nombre": r["prenda_nombre"],
                "talla": r["talla"],
                "color": r["color"],
                "precio_venta": r["precio_venta"],
                "stock_disponible": r["stock_disponible"],
            }
            for r in rows
        ]

        return {"total": total, "page": page, "page_size": page_size, "items": items}


# ---------------------------------------------------------------------------
# Creación de Venta POS (Efectivo, Tarjeta, QR)
# ---------------------------------------------------------------------------

async def crear_venta_pos(
    empresa_id: str,
    user_id: str,
    rol: str,
    idempotency_key: str,
    items: list[dict],
    cliente: dict,
    pago: dict,
    sucursal_solicitada: Optional[str] = None,
    device_serial: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    """
    Realiza una venta directa en caja.
    Cumple atomicidad RNF04, idempotencia RNF05 y auditoría BR-13/BR-14.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        # 1. Idempotencia: Verificar si ya existe una venta con ese idempotency_key
        venta_existente = await conn.fetchrow(
            """
            SELECT v.id, v.numero, v.total, v.estado, p.metodo, p.monto
              FROM venta v
              LEFT JOIN pago p ON p.venta_id = v.id
             WHERE v.empresa_id = $1 AND v.idempotency_key = $2
            """,
            UUID(empresa_id),
            idempotency_key,
        )
        if venta_existente:
            return {
                "venta_id": str(venta_existente["id"]),
                "numero": venta_existente["numero"],
                "total": venta_existente["total"],
                "cambio": Decimal("0.00"),
                "metodo_pago": venta_existente["metodo"] or "efectivo",
                "estado": venta_existente["estado"],
                "comprobante_url": f"/api/v1/ventas/{venta_existente['id']}/ticket",
            }

        # 2. Determinar sucursal del cajero y validar dispositivo
        sucursal_id = await _resolver_sucursal_cajero(conn, empresa_id, user_id, rol, sucursal_solicitada)
        dispositivo_id = await _validar_dispositivo_pos(conn, empresa_id, sucursal_id, device_serial)

        # 3. Validar cliente y datos de facturación
        tipo_cliente = cliente.get("tipo", "consumidor_final")
        cliente_nombre = "Consumidor Final"
        cliente_documento = "0"
        if tipo_cliente == "identificado":
            cliente_nombre = (cliente.get("nombre") or "").strip()
            cliente_documento = (cliente.get("documento") or "").strip()
            if not cliente_nombre or not cliente_documento:
                raise api_error(422, "DATOS_FACTURACION_INCOMPLETOS", "Debe proporcionar nombre y documento del cliente")

        # 4. Cargar variantes y calcular subtotales
        variante_ids = [UUID(str(it["variante_id"])) for it in items]
        variantes_db = await conn.fetch(
            """
            SELECT id, precio_venta, sku
              FROM variante
             WHERE id = ANY($1::uuid[]) AND empresa_id = $2 AND deleted_at IS NULL
            """,
            variante_ids,
            UUID(empresa_id),
        )
        variantes_dict = {str(r["id"]): r for r in variantes_db}

        if len(variantes_dict) != len(set(str(it["variante_id"]) for it in items)):
            raise api_error(404, "VARIANTE_NO_VALIDA", "Una o más variantes no pertenecen al tenant o no existen")

        subtotal_acumulado = Decimal("0.00")
        descuento_acumulado = Decimal("0.00")
        lineas_procesadas = []

        for it in items:
            var_id_str = str(it["variante_id"])
            var_info = variantes_dict[var_id_str]
            cant = int(it["cantidad"])
            if cant <= 0:
                raise api_error(422, "CANTIDAD_INVALIDA", "La cantidad debe ser mayor a 0")

            precio_lista = Decimal(str(var_info["precio_venta"]))
            descuento_linea = Decimal(str(it.get("descuento_linea") or "0.00"))
            subtotal_linea = (precio_lista * cant) - descuento_linea
            if subtotal_linea < 0:
                raise api_error(422, "DESCUENTO_EXCESIVO", "El descuento no puede superar el precio del artículo")

            subtotal_acumulado += precio_lista * cant
            descuento_acumulado += descuento_linea

            lineas_procesadas.append({
                "variante_id": UUID(var_id_str),
                "cantidad": cant,
                "precio_lista": precio_lista,
                "precio_unitario": precio_lista,
                "descuento_linea": descuento_linea,
                "subtotal": subtotal_linea,
            })

        # Regla contable: total = subtotal - descuento + impuesto
        impuesto_calculado = (subtotal_acumulado - descuento_acumulado) * TASA_IVA
        total_a_pagar = (subtotal_acumulado - descuento_acumulado) + impuesto_calculado

        metodo_pago = pago.get("metodo", "efectivo")
        monto_recibido = Decimal(str(pago.get("monto_recibido") or "0.00"))
        cambio = Decimal("0.00")

        # 5. Validaciones según método de pago
        if metodo_pago == "efectivo":
            if monto_recibido < total_a_pagar:
                faltante = total_a_pagar - monto_recibido
                raise api_error(
                    422,
                    "SALDO_INSUFICIENTE",
                    f"Efectivo insuficiente. Total: {total_a_pagar:.2f}, Recibido: {monto_recibido:.2f}, Faltante: {faltante:.2f}",
                )
            cambio = monto_recibido - total_a_pagar
        elif metodo_pago == "qr":
            referencia = pago.get("referencia")
            if not referencia or not referencia.strip():
                raise api_error(422, "REFERENCIA_REQUERIDA", "El pago QR requiere código o número de referencia bancaria")
        elif metodo_pago == "tarjeta":
            pass  # Será redirigido a Stripe
        else:
            raise api_error(422, "METODO_NO_SOPORTADO", f"Método de pago '{metodo_pago}' no soportado")

        # 6. Generar correlativo de venta
        correlativo_val = await conn.fetchval(
            "SELECT COUNT(*) + 1 FROM venta WHERE empresa_id = $1", UUID(empresa_id)
        )
        prefijo_suc = sucursal_id[:4].upper()
        numero_venta = f"POS-{prefijo_suc}-{correlativo_val:05d}"

        # 7. Si es Tarjeta, crear venta en 'pendiente_pago' y delegar a pago_service
        if metodo_pago == "tarjeta":
            venta_row = await conn.fetchrow(
                """
                INSERT INTO venta (
                    empresa_id, numero, sucursal_id, cajero_id, canal,
                    subtotal, descuento, impuesto, total, estado,
                    idempotency_key, cliente_nombre, cliente_documento,
                    dispositivo_id, moneda
                )
                VALUES (
                    $1, $2, $3, $4, 'POS',
                    $5, $6, $7, $8, 'pendiente_pago',
                    $9, $10, $11, $12, 'BOB'
                )
                RETURNING id
                """,
                UUID(empresa_id),
                numero_venta,
                UUID(sucursal_id),
                UUID(user_id),
                subtotal_acumulado,
                descuento_acumulado,
                impuesto_calculado,
                total_a_pagar,
                idempotency_key,
                cliente_nombre,
                cliente_documento,
                UUID(dispositivo_id) if dispositivo_id else None,
            )
            venta_id = venta_row["id"]

            for lin in lineas_procesadas:
                await conn.execute(
                    """
                    INSERT INTO venta_detalle (
                        empresa_id, venta_id, variante_id, cantidad,
                        precio_lista, precio_unitario, descuento_linea, subtotal
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    UUID(empresa_id),
                    venta_id,
                    lin["variante_id"],
                    lin["cantidad"],
                    lin["precio_lista"],
                    lin["precio_unitario"],
                    lin["descuento_linea"],
                    lin["subtotal"],
                )

            # Delegar intención en pago_service
            from app.services import pago_service
            intencion = await pago_service.crear_intencion_pago(
                empresa_id=empresa_id,
                user_id=user_id,
                rol=rol,
                venta_id=str(venta_id),
                idempotency_key=f"card_{idempotency_key}",
                ip=ip,
            )

            return {
                "venta_id": str(venta_id),
                "numero": numero_venta,
                "total": total_a_pagar,
                "cambio": Decimal("0.00"),
                "metodo_pago": "tarjeta",
                "estado": "pendiente_pago",
                "intencion_pago": intencion,
                "comprobante_url": f"/api/v1/ventas/{venta_id}/ticket",
            }

        # 8. Para Efectivo y QR: ATOMICIDAD TOTAL (Bloqueo de inventario + Descuento + Venta + Pago + Kárdex)
        # Ordenar variante_ids para prevenir deadlocks (RNF04)
        variantes_ordenadas = sorted(lineas_procesadas, key=lambda x: str(x["variante_id"]))

        # Bloquear filas de inventario
        var_uuids_sorted = [x["variante_id"] for x in variantes_ordenadas]
        inv_rows = await conn.fetch(
            """
            SELECT variante_id, stock_fisico, stock_reservado, stock_disponible
              FROM inventario
             WHERE empresa_id = $1 AND sucursal_id = $2 AND variante_id = ANY($3::uuid[])
             FOR UPDATE
            """,
            UUID(empresa_id),
            UUID(sucursal_id),
            var_uuids_sorted,
        )
        inv_dict = {str(r["variante_id"]): r for r in inv_rows}

        faltantes = []
        for lin in variantes_ordenadas:
            vid_str = str(lin["variante_id"])
            stock_info = inv_dict.get(vid_str)
            disp = stock_info["stock_disponible"] if stock_info else 0
            if disp < lin["cantidad"]:
                faltantes.append({
                    "variante_id": vid_str,
                    "solicitado": lin["cantidad"],
                    "disponible": disp,
                })

        if faltantes:
            raise api_error(
                409,
                "STOCK_INSUFICIENTE",
                f"Existencias insuficientes en sucursal para: {faltantes}",
            )

        # Generar firma criptográfica para QR
        qr_nonce = secrets.token_hex(8)
        ahora_iso = conn.fetchval("SELECT now()::text")
        firma_qr = _generar_firma_pos(empresa_id, numero_venta, total_a_pagar, str(ahora_iso), qr_nonce)

        # Insertar venta en 'completada'
        venta_row = await conn.fetchrow(
            """
            INSERT INTO venta (
                empresa_id, numero, sucursal_id, cajero_id, canal,
                subtotal, descuento, impuesto, total, estado,
                idempotency_key, firma_qr, qr_nonce, firma_algoritmo,
                cliente_nombre, cliente_documento, dispositivo_id, moneda
            )
            VALUES (
                $1, $2, $3, $4, 'POS',
                $5, $6, $7, $8, 'completada',
                $9, $10, $11, 'HMAC-SHA256',
                $12, $13, $14, 'BOB'
            )
            RETURNING id, created_at
            """,
            UUID(empresa_id),
            numero_venta,
            UUID(sucursal_id),
            UUID(user_id),
            subtotal_acumulado,
            descuento_acumulado,
            impuesto_calculado,
            total_a_pagar,
            idempotency_key,
            firma_qr,
            qr_nonce,
            cliente_nombre,
            cliente_documento,
            UUID(dispositivo_id) if dispositivo_id else None,
        )
        venta_id = venta_row["id"]

        # Insertar venta_detalle y descontar inventario con Kárdex
        for lin in variantes_ordenadas:
            await conn.execute(
                """
                INSERT INTO venta_detalle (
                    empresa_id, venta_id, variante_id, cantidad,
                    precio_lista, precio_unitario, descuento_linea, subtotal
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                UUID(empresa_id),
                venta_id,
                lin["variante_id"],
                lin["cantidad"],
                lin["precio_lista"],
                lin["precio_unitario"],
                lin["descuento_linea"],
                lin["subtotal"],
            )

            vid_str = str(lin["variante_id"])
            stock_prev = inv_dict[vid_str]["stock_fisico"]
            stock_post = stock_prev - lin["cantidad"]

            # Actualizar inventario físico
            await conn.execute(
                """
                UPDATE inventario
                   SET stock_fisico = stock_fisico - $1,
                       actualizado_en = now()
                 WHERE empresa_id = $2 AND sucursal_id = $3 AND variante_id = $4
                """,
                lin["cantidad"],
                UUID(empresa_id),
                UUID(sucursal_id),
                lin["variante_id"],
            )

            # Insertar movimiento kárdex (particionado)
            await conn.execute(
                """
                INSERT INTO movimiento_inventario (
                    empresa_id, variante_id, sucursal_id, tipo,
                    cantidad, stock_anterior, stock_nuevo,
                    referencia_tipo, referencia_id, motivo, usuario_id
                )
                VALUES (
                    $1, $2, $3, 'venta',
                    $4, $5, $6,
                    'venta_pos', $7, 'Venta presencial en mostrador', $8
                )
                """,
                UUID(empresa_id),
                lin["variante_id"],
                UUID(sucursal_id),
                -lin["cantidad"],
                stock_prev,
                stock_post,
                venta_id,
                UUID(user_id),
            )

        # Insertar pago completado
        await conn.execute(
            """
            INSERT INTO pago (
                empresa_id, venta_id, monto, moneda, metodo,
                idempotency_key, estado, referencia, pagado_en
            )
            VALUES ($1, $2, $3, 'BOB', $4, $5, 'completado', $6, now())
            """,
            UUID(empresa_id),
            venta_id,
            total_a_pagar,
            metodo_pago,
            f"pago_{idempotency_key}",
            pago.get("referencia") or f"Cobro en mostrador ({metodo_pago})",
        )

        # Historial de estado
        await conn.execute(
            """
            INSERT INTO venta_estado_historial (
                empresa_id, venta_id, estado_anterior, estado_nuevo, motivo, usuario_id
            )
            VALUES ($1, $2, NULL, 'completada', 'Venta y cobro directo en POS', $3)
            """,
            UUID(empresa_id),
            venta_id,
            UUID(user_id),
        )

    # Auditoría
    actor_tipo = "superadmin" if rol == "superadmin" else "usuario"
    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo=actor_tipo,
        accion="insert",
        entidad="venta",
        entidad_id=str(venta_id),
        datos_despues={
            "numero": numero_venta,
            "total": str(total_a_pagar),
            "canal": "POS",
            "metodo_pago": metodo_pago,
            "cambio": str(cambio),
        },
        ip=ip,
        es_accion_superadmin=(rol == "superadmin"),
    )

    return {
        "venta_id": str(venta_id),
        "numero": numero_venta,
        "total": total_a_pagar,
        "cambio": cambio,
        "metodo_pago": metodo_pago,
        "estado": "completada",
        "comprobante_url": f"/api/v1/ventas/{venta_id}/ticket",
    }


async def get_ticket_data(empresa_id: str, user_id: str, rol: str, venta_id: str) -> dict:
    """Obtiene los datos formateados para impresión de ticket térmico (80mm)."""
    async with tenant_connection(empresa_id, user_id) as conn:
        venta = await conn.fetchrow(
            """
            SELECT v.id, v.numero, v.canal, v.estado,
                   v.subtotal, v.descuento, v.impuesto, v.total,
                   v.cliente_nombre, v.cliente_documento,
                   v.firma_qr, v.fecha_hora,
                   e.nombre AS empresa_nombre, e.nit AS empresa_nit,
                   s.nombre AS sucursal_nombre, s.direccion AS sucursal_direccion
              FROM venta v
              JOIN empresa e ON e.id = v.empresa_id
              LEFT JOIN sucursal s ON s.id = v.sucursal_id
             WHERE v.id = $1 AND v.empresa_id = $2
            """,
            UUID(venta_id),
            UUID(empresa_id),
        )
        if not venta:
            raise api_error(404, "VENTA_NO_ENCONTRADA", "Ticket no encontrado")

        pago = await conn.fetchrow(
            "SELECT metodo, monto, referencia FROM pago WHERE venta_id = $1 AND empresa_id = $2 LIMIT 1",
            UUID(venta_id),
            UUID(empresa_id),
        )

        detalles = await conn.fetch(
            """
            SELECT vd.cantidad, vd.precio_unitario, vd.subtotal,
                   p.nombre AS prenda_nombre, t.nombre AS talla, c.nombre AS color
              FROM venta_detalle vd
              JOIN variante v ON v.id = vd.variante_id
              JOIN prenda p ON p.id = v.prenda_id
              JOIN talla t ON t.id = v.talla_id
              JOIN color c ON c.id = v.color_id
             WHERE vd.venta_id = $1 AND vd.empresa_id = $2
            """,
            UUID(venta_id),
            UUID(empresa_id),
        )

        return {
            "ticket": {
                "empresa": venta["empresa_nombre"],
                "nit": venta["empresa_nit"],
                "sucursal": venta["sucursal_nombre"],
                "direccion": venta["sucursal_direccion"],
                "numero": venta["numero"],
                "fecha": venta["fecha_hora"],
                "cliente": venta["cliente_nombre"],
                "documento": venta["cliente_documento"],
                "subtotal": venta["subtotal"],
                "descuento": venta["descuento"],
                "impuesto": venta["impuesto"],
                "total": venta["total"],
                "metodo_pago": pago["metodo"] if pago else "efectivo",
                "firma_qr": venta["firma_qr"],
                "items": [
                    {
                        "prenda": d["prenda_nombre"],
                        "talla": d["talla"],
                        "color": d["color"],
                        "cantidad": d["cantidad"],
                        "precio_unitario": d["precio_unitario"],
                        "subtotal": d["subtotal"],
                    }
                    for d in detalles
                ],
            }
        }



class PosService:
    def __init__(self, pool=None):
        self.pool = pool

    async def buscar_variante_barcode(self, empresa_id: str, barcode: str):
        return await buscar_por_barcode(empresa_id=empresa_id, barcode=barcode)

    async def procesar_venta_pos(self, empresa_id: str, usuario_id: str, datos=None):
        return await crear_venta_pos(empresa_id=empresa_id, user_id=usuario_id, req=datos)
