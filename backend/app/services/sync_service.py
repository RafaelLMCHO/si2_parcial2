import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from uuid import NAMESPACE_URL, UUID, uuid5
from asyncpg import Pool
from fastapi import HTTPException

from app.schemas.sync import (
    CatalogoOfflinePackage,
    SoftLockCreate,
    SoftLockResponse,
    SoftLockListItem,
    NotaCambioCreate,
    SyncBatchRequest,
    SyncBatchResponse,
    ConflictoSyncItem,
    ResolucionConflictoRequest
)

SECRET_KEY_QR = "fashionstore_offline_secret_key_2026"


def _op_get(op, name: str, default=None):
    """Accede a operaciones que pueden ser Pydantic, dict o asyncpg.Record."""
    if isinstance(op, dict):
        return op.get(name, default)
    try:
        if hasattr(op, "__contains__") and name in op:
            return op[name]
    except TypeError:
        pass
    return getattr(op, name, default)


def _coerce_uuid_str(raw: Any, namespace_prefix: str = "op") -> str:
    """Garantiza un UUID valido incluso si un cliente antiguo envio un ID legible."""
    text = str(raw or "").strip()
    if text:
        try:
            return str(UUID(text))
        except (ValueError, TypeError):
            pass
    return str(uuid5(NAMESPACE_URL, f"{namespace_prefix}:{text or 'empty'}"))


class SyncService:
    def __init__(self, pool: Pool):
        self.pool = pool

    # =========================================================================
    # CU-25: Descargar catálogo offline optimizado
    # =========================================================================
    async def descargar_catalogo_offline(
        self, empresa_id: str, sucursal_id: Optional[str] = None
    ) -> CatalogoOfflinePackage:
        async with self.pool.acquire() as conn:
            # 0. Sucursales activas (accesible tambien para clientes sin requerir rol admin)
            if sucursal_id:
                sucursales_rows = await conn.fetch(
                    """
                    SELECT s.id, s.nombre, s.direccion, ci.nombre AS ciudad, s.es_matriz
                    FROM sucursal s
                    LEFT JOIN ciudad ci ON ci.id = s.ciudad_id
                    WHERE s.empresa_id = $1 AND s.id = $2
                      AND s.estado = 'activa' AND s.deleted_at IS NULL
                    ORDER BY s.es_matriz DESC, s.nombre ASC
                    """,
                    empresa_id, sucursal_id
                )
            else:
                sucursales_rows = await conn.fetch(
                    """
                    SELECT s.id, s.nombre, s.direccion, ci.nombre AS ciudad, s.es_matriz
                    FROM sucursal s
                    LEFT JOIN ciudad ci ON ci.id = s.ciudad_id
                    WHERE s.empresa_id = $1 AND s.estado = 'activa' AND s.deleted_at IS NULL
                    ORDER BY s.es_matriz DESC, s.nombre ASC
                    """,
                    empresa_id
                )
            sucursales = [dict(r) for r in sucursales_rows]
            for s in sucursales:
                if s.get("id") is not None:
                    s["id"] = str(s["id"])
                if s.get("direccion") is None:
                    s["direccion"] = ""
                if s.get("ciudad") is None:
                    s["ciudad"] = ""

            # 1. Prendas activas
            prendas_rows = await conn.fetch(
                """
                SELECT id, codigo, nombre, descripcion, precio_base, categoria_id, imagen_url
                FROM prenda
                WHERE empresa_id = $1 AND estado = 'activa' AND deleted_at IS NULL
                ORDER BY nombre ASC
                """,
                empresa_id
            )
            prendas = [dict(r) for r in prendas_rows]

            # 2. Variantes activas
            variantes_rows = await conn.fetch(
                """
                SELECT v.id, v.prenda_id, v.sku, v.precio_venta, v.codigo_barras,
                       t.nombre as talla, c.nombre as color, c.hex as color_hex
                FROM variante v
                LEFT JOIN talla t ON t.id = v.talla_id
                LEFT JOIN color c ON c.id = v.color_id
                WHERE v.empresa_id = $1 AND v.estado = 'activa' AND v.deleted_at IS NULL
                """,
                empresa_id
            )
            variantes = [dict(r) for r in variantes_rows]

            # 3. Existencias de la sucursal (o globales)
            if sucursal_id:
                existencias_rows = await conn.fetch(
                    """
                    SELECT variante_id, sucursal_id, stock_disponible, stock_minimo, ubicacion
                    FROM inventario
                    WHERE empresa_id = $1 AND sucursal_id = $2
                    """,
                    empresa_id, sucursal_id
                )
            else:
                existencias_rows = await conn.fetch(
                    """
                    SELECT variante_id, sucursal_id, stock_disponible, stock_minimo, ubicacion
                    FROM inventario
                    WHERE empresa_id = $1
                    """,
                    empresa_id
                )
            existencias = [dict(r) for r in existencias_rows]

            for item in existencias:
                if "variante_id" in item:
                    item["variante_id"] = str(item["variante_id"])
                if "sucursal_id" in item:
                    item["sucursal_id"] = str(item["sucursal_id"])

            for p in prendas:
                p["id"] = str(p["id"])
                if p.get("categoria_id"):
                    p["categoria_id"] = str(p["categoria_id"])
                if p.get("precio_base"):
                    p["precio_base"] = float(p["precio_base"])

            for v in variantes:
                if v.get("id"):
                    v["id"] = str(v["id"])
                if v.get("prenda_id"):
                    v["prenda_id"] = str(v["prenda_id"])
                if v.get("precio_venta"):
                    v["precio_venta"] = float(v["precio_venta"])

            return CatalogoOfflinePackage(
                empresa_id=str(empresa_id),
                sucursal_id=str(sucursal_id) if sucursal_id else None,
                generado_en=datetime.now(timezone.utc),
                sucursales=sucursales,
                prendas=prendas,
                variantes=variantes,
                existencias=existencias,
                total_articulos=len(variantes)
            )

    # =========================================================================
    # CU-27: Soft-Lock local / temporal con TTL de 45 minutos
    # =========================================================================
    async def crear_soft_lock(self, empresa_id: str, datos: SoftLockCreate) -> SoftLockResponse:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Limpiar soft-locks vencidos primero
                await conn.execute(
                    "DELETE FROM soft_lock WHERE empresa_id = $1 AND expira_en < NOW()",
                    empresa_id
                )

                # Verificar stock disponible real
                stock = await conn.fetchrow(
                    """
                    SELECT i.stock_disponible,
                           COALESCE((SELECT SUM(sl.cantidad) FROM soft_lock sl 
                                     WHERE sl.empresa_id = $1 AND sl.sucursal_id = $2 
                                       AND sl.variante_id = $3 AND sl.expira_en > NOW()), 0) as bloqueado
                    FROM inventario i
                    WHERE i.empresa_id = $1 AND i.sucursal_id = $2 AND i.variante_id = $3
                    FOR UPDATE
                    """,
                    empresa_id, datos.sucursal_id, datos.variante_id
                )

                if not stock:
                    raise HTTPException(status_code=404, detail="Inventario no encontrado para la sucursal")

                disponible_neto = stock["stock_disponible"] - stock["bloqueado"]
                if disponible_neto < datos.cantidad:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Stock insuficiente para soft-lock. Disponible neto: {disponible_neto}, solicitado: {datos.cantidad}"
                    )

                expira_en = datetime.now(timezone.utc) + timedelta(minutes=datos.ttl_minutos)
                lock_id = await conn.fetchval(
                    """
                    INSERT INTO soft_lock (empresa_id, sucursal_id, variante_id, dispositivo_id, cantidad, expira_en)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    empresa_id, datos.sucursal_id, datos.variante_id, datos.dispositivo_id, datos.cantidad, expira_en
                )

                return SoftLockResponse(
                    id=str(lock_id),
                    sucursal_id=datos.sucursal_id,
                    variante_id=datos.variante_id,
                    cantidad=datos.cantidad,
                    expira_en=expira_en,
                    activo=True
                )

    async def listar_soft_locks(
        self, empresa_id: str, sucursal_id: Optional[str] = None
    ) -> List[SoftLockListItem]:
        now_utc = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM soft_lock WHERE empresa_id = $1 AND expira_en <= NOW()",
                empresa_id,
            )

            query = """
                SELECT sl.id, sl.sucursal_id, s.nombre AS sucursal_nombre,
                       sl.variante_id, v.sku, p.nombre AS prenda_nombre,
                       t.nombre AS talla, c.nombre AS color,
                       sl.dispositivo_id, sl.cantidad, sl.expira_en, sl.creado_en
                FROM soft_lock sl
                LEFT JOIN sucursal s ON s.id = sl.sucursal_id
                LEFT JOIN variante v ON v.id = sl.variante_id
                LEFT JOIN prenda p ON p.id = v.prenda_id
                LEFT JOIN talla t ON t.id = v.talla_id
                LEFT JOIN color c ON c.id = v.color_id
                WHERE sl.empresa_id = $1 AND sl.expira_en > NOW()
            """
            params: List[Any] = [empresa_id]
            if sucursal_id:
                query += " AND sl.sucursal_id = $2"
                params.append(sucursal_id)
            query += " ORDER BY sl.expira_en ASC"

            rows = await conn.fetch(query, *params)
            items: List[SoftLockListItem] = []
            for r in rows:
                item = dict(r)
                expira_en = item.get("expira_en")
                creado_en = item.get("creado_en") or now_utc
                if isinstance(expira_en, str):
                    expira_en = datetime.fromisoformat(expira_en.replace("Z", "+00:00"))
                if expira_en.tzinfo is None:
                    expira_en = expira_en.replace(tzinfo=timezone.utc)
                if isinstance(creado_en, str):
                    creado_en = datetime.fromisoformat(creado_en.replace("Z", "+00:00"))
                if creado_en.tzinfo is None:
                    creado_en = creado_en.replace(tzinfo=timezone.utc)
                ttl_seg = max(0, int((expira_en - now_utc).total_seconds()))
                items.append(
                    SoftLockListItem(
                        id=str(item["id"]),
                        sucursal_id=str(item["sucursal_id"]),
                        sucursal_nombre=item.get("sucursal_nombre"),
                        variante_id=str(item["variante_id"]),
                        sku=item.get("sku"),
                        prenda_nombre=item.get("prenda_nombre"),
                        talla=item.get("talla"),
                        color=item.get("color"),
                        dispositivo_id=str(item.get("dispositivo_id") or "DEFAULT_DEVICE"),
                        cantidad=int(item.get("cantidad") or 0),
                        expira_en=expira_en,
                        creado_en=creado_en,
                        ttl_restante_segundos=ttl_seg,
                        activo=ttl_seg > 0,
                    )
                )
            return items

    async def liberar_soft_lock(self, empresa_id: str, lock_id: str) -> dict:
        try:
            UUID(str(lock_id))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Identificador de bloqueo inválido")

        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    DELETE FROM soft_lock
                    WHERE id = $1 AND empresa_id = $2
                    RETURNING id
                    """,
                    lock_id,
                    empresa_id,
                )
            except Exception as exc:
                if "uuid" in str(exc).lower() or "DataError" in type(exc).__name__:
                    raise HTTPException(status_code=400, detail="Identificador de bloqueo inválido")
                raise

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="Soft-lock no encontrado o ya expirado",
                )
            return {
                "id": str(row["id"]),
                "liberado": True,
                "mensaje": "Bloqueo temporal liberado correctamente",
            }

    # =========================================================================
    # CU-29: Validar comprobante y procesar cambio mediante QR offline
    # =========================================================================
    def generar_firma_qr_ticket(self, payload: dict) -> str:
        data_str = f"{payload.get('uuid')}|{payload.get('fecha_hora_local')}|{payload.get('total')}|{payload.get('usuario_id')}"
        return hmac.new(SECRET_KEY_QR.encode(), data_str.encode(), hashlib.sha256).hexdigest()

    async def validar_qr_comprobante(self, empresa_id: str, qr_data: str) -> dict:
        try:
            payload = json.loads(qr_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Estructura de código QR inválida")

        firma = payload.get("firma")
        if not firma:
            raise HTTPException(status_code=400, detail="Código QR carece de firma criptográfica")

        firma_esperada = self.generar_firma_qr_ticket(payload)
        if not hmac.compare_digest(firma, firma_esperada):
            raise HTTPException(status_code=403, detail="Firma de comprobante alterada o ilegítima (QR inválido)")

        # Validar plazo comercial de 30 días (BR-10)
        fecha_str = payload.get("fecha_hora_local")
        if fecha_str:
            fecha_emision = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
            dias_transcurridos = (datetime.now(timezone.utc) - fecha_emision).days
            if dias_transcurridos > 30:
                raise HTTPException(
                    status_code=400,
                    detail=f"Plazo legal de cambio expirado: {dias_transcurridos} días transcurridos (máximo 30 días BR-10)"
                )

        return {
            "valido": True,
            "uuid": payload.get("uuid"),
            "fecha_emision": fecha_str,
            "total": payload.get("total"),
            "lineas": payload.get("lineas", []),
            "cliente_nombre": payload.get("cliente_nombre")
        }

    async def procesar_nota_cambio(
        self, empresa_id: str, usuario_id: str, datos: NotaCambioCreate
    ) -> dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Verificar stock de variante nueva
                stock_nueva = await conn.fetchrow(
                    """
                    SELECT stock_disponible FROM inventario
                    WHERE empresa_id = $1 AND sucursal_id = $2 AND variante_id = $3
                    FOR UPDATE
                    """,
                    empresa_id, datos.sucursal_id, datos.variante_nueva_id
                )
                if not stock_nueva or stock_nueva["stock_disponible"] < datos.cantidad:
                    raise HTTPException(status_code=409, detail="Stock insuficiente de la prenda nueva sustituta")

                # Reingresar prenda devuelta al stock
                await conn.execute(
                    """
                    UPDATE inventario
                    SET stock_fisico = stock_fisico + $1
                    WHERE empresa_id = $2 AND sucursal_id = $3 AND variante_id = $4
                    """,
                    datos.cantidad, empresa_id, datos.sucursal_id, datos.variante_devuelta_id
                )

                # Descontar prenda nueva del stock
                await conn.execute(
                    """
                    UPDATE inventario
                    SET stock_fisico = stock_fisico - $1
                    WHERE empresa_id = $2 AND sucursal_id = $3 AND variante_id = $4
                    """,
                    datos.cantidad, empresa_id, datos.sucursal_id, datos.variante_nueva_id
                )

                # Insertar nota de cambio
                nota_id = await conn.fetchval(
                    """
                    INSERT INTO nota_cambio (
                        empresa_id, sucursal_id, venta_origen_id,
                        variante_devuelta_id, variante_nueva_id, cantidad,
                        motivo, cajero_id, qr_firma
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    empresa_id, datos.sucursal_id, datos.venta_origen_id,
                    datos.variante_devuelta_id, datos.variante_nueva_id,
                    datos.cantidad, datos.motivo, usuario_id, datos.qr_firma
                )

                return {
                    "nota_cambio_id": str(nota_id),
                    "estado": "confirmada",
                    "mensaje": "Cambio de prenda procesado y stock regularizado"
                }

    # =========================================================================
    # CU-31: Sincronización por Lote con Idempotencia (RNF05)
    # =========================================================================
    async def procesar_lote_sync(
        self, empresa_id: str, usuario_id: str, lote: SyncBatchRequest
    ) -> SyncBatchResponse:
        confirmados: List[str] = []
        conflictos: List[ConflictoSyncItem] = []

        async with self.pool.acquire() as conn:
            for op in lote.operaciones:
                op_db_id = _coerce_uuid_str(op.id, op.tipo)
                # 1. Idempotencia RNF05: ¿ya fue procesada previamente?
                previo = await conn.fetchrow(
                    """
                    SELECT resultado_json FROM sync_registro_idempotencia
                    WHERE empresa_id = $1 AND idempotency_key = $2
                    """,
                    empresa_id, op.idempotency_key
                )
                if previo:
                    confirmados.append(op.id)
                    continue

                # 2. Procesar según tipo de operación
                try:
                    try:
                        UUID(str(op.sucursal_id))
                    except (ValueError, TypeError):
                        raise Exception(f"Sucursal inválida en operación offline: {op.sucursal_id}")

                    async with conn.transaction():
                        if op.tipo == "venta_offline":
                            await self._procesar_venta_offline_sync(conn, empresa_id, usuario_id, op)
                        elif op.tipo == "reserva_offline":
                            await self._procesar_reserva_offline_sync(conn, empresa_id, usuario_id, op)
                        elif op.tipo == "cambio_offline":
                            await self._procesar_cambio_offline_sync(conn, empresa_id, usuario_id, op)
                        else:
                            raise Exception(f"Tipo de operación offline no soportada: {op.tipo}")

                        # Guardar idempotencia
                        resultado = {"status": "confirmada", "op_id": op.id, "op_db_id": op_db_id}
                        await conn.execute(
                            """
                            INSERT INTO sync_registro_idempotencia (empresa_id, idempotency_key, tipo_operacion, resultado_json)
                            VALUES ($1, $2, $3, $4)
                            """,
                            empresa_id, op.idempotency_key, op.tipo, json.dumps(resultado)
                        )

                        # Registrar o actualizar operacion_pendiente como 'aplicada'
                        await conn.execute(
                            """
                            INSERT INTO operacion_pendiente (
                                id, empresa_id, sucursal_id, usuario_id, tipo,
                                payload, idempotency_key, estado, procesada_en
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'aplicada', NOW())
                            ON CONFLICT (empresa_id, id) DO UPDATE
                            SET estado = 'aplicada', procesada_en = NOW()
                            """,
                            op_db_id, empresa_id, op.sucursal_id, usuario_id, op.tipo,
                            json.dumps(op.payload), op.idempotency_key
                        )

                        confirmados.append(op.id)
                except Exception as ex:
                    # Registrar en conflicto sin anular el resto del lote
                    err_msg = str(ex)
                    try:
                        UUID(str(op.sucursal_id))
                        await conn.execute(
                            """
                            INSERT INTO operacion_pendiente (
                                id, empresa_id, sucursal_id, usuario_id, tipo,
                                payload, idempotency_key, estado, ultimo_error
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'conflicto', $8)
                            ON CONFLICT (empresa_id, id) DO UPDATE
                            SET estado = 'conflicto', ultimo_error = $8
                            """,
                            op_db_id, empresa_id, op.sucursal_id, usuario_id, op.tipo,
                            json.dumps(op.payload), op.idempotency_key, err_msg
                        )
                    except Exception:
                        pass
                    conflictos.append(ConflictoSyncItem(
                        id=op.id,
                        tipo=op.tipo,
                        causa="stock_insuficiente" if "Stock" in err_msg else "error_validacion",
                        detalle=err_msg
                    ))

        return SyncBatchResponse(
            confirmados=confirmados,
            conflictos=conflictos,
            procesados_total=len(lote.operaciones)
        )

    async def _procesar_venta_offline_sync(self, conn, empresa_id: str, usuario_id: str, op):
        op_id = _coerce_uuid_str(_op_get(op, "id"), "venta_offline")
        sucursal_id = _op_get(op, "sucursal_id")
        op_usuario_id = str(_op_get(op, "usuario_id") or usuario_id)
        try:
            UUID(op_usuario_id)
        except (ValueError, TypeError):
            op_usuario_id = str(usuario_id)
        p = _op_get(op, "payload") or {}
        if isinstance(p, str):
            p = json.loads(p)
        lineas = p.get("lineas", [])
        if not lineas:
            raise Exception("Venta offline sin líneas de productos")

        # Bloquear y verificar stock de todas las líneas en orden
        lineas_ordenadas = sorted(lineas, key=lambda x: str(x["variante_id"]))
        for linea in lineas_ordenadas:
            var_id = linea["variante_id"]
            cant = int(linea["cantidad"])
            stock = await conn.fetchrow(
                """
                SELECT stock_disponible FROM inventario
                WHERE empresa_id = $1 AND sucursal_id = $2 AND variante_id = $3
                FOR UPDATE
                """,
                empresa_id, sucursal_id, var_id
            )
            if not stock or stock["stock_disponible"] < cant:
                raise Exception(f"Stock insuficiente en servidor para variante {var_id}")

            # Descontar stock
            await conn.execute(
                """
                UPDATE inventario
                SET stock_fisico = stock_fisico - $1, actualizado_en = now()
                WHERE empresa_id = $2 AND sucursal_id = $3 AND variante_id = $4
                """,
                cant, empresa_id, sucursal_id, var_id
            )

        # Insertar venta oficial
        total = float(p.get("total", 0.0))
        numero_ticket = f"OFF-{str(op_id)[:8].upper()}"
        venta_id = await conn.fetchval(
            """
            INSERT INTO venta (
                id, empresa_id, sucursal_id, usuario_id, numero,
                subtotal, descuento, impuesto, total, estado, canal,
                idempotency_key, cliente_nombre, cliente_documento
            ) VALUES ($1, $2, $3, $4, $5, $6, 0, 0, $6, 'completada', 'OFFLINE', $7, $8, $9)
            RETURNING id
            """,
            op_id, empresa_id, sucursal_id, op_usuario_id, numero_ticket,
            total, f"offline_{op_id}", p.get("cliente_nombre", "Consumidor Final"),
            p.get("cliente_documento", "0")
        )

        for l in lineas:
            cant = int(l["cantidad"])
            pu = float(l["precio_unitario"])
            await conn.execute(
                """
                INSERT INTO venta_detalle (
                    empresa_id, venta_id, variante_id, cantidad,
                    precio_lista, precio_unitario, descuento_linea, subtotal
                )
                VALUES ($1, $2, $3, $4, $5, $5, 0, $6)
                """,
                empresa_id, venta_id, l["variante_id"], cant, pu, cant * pu
            )

    async def _procesar_reserva_offline_sync(self, conn, empresa_id: str, usuario_id: str, op):
        op_id = _coerce_uuid_str(_op_get(op, "id"), "reserva_offline")
        sucursal_id = _op_get(op, "sucursal_id")
        op_usuario_id = str(_op_get(op, "usuario_id") or usuario_id)
        try:
            UUID(op_usuario_id)
        except (ValueError, TypeError):
            op_usuario_id = str(usuario_id)
        p = _op_get(op, "payload") or {}
        if isinstance(p, str):
            p = json.loads(p)
        items = p.get("items", [])
        if not items:
            raise Exception("Reserva offline sin ítems")

        cantidades: Dict[str, int] = {}
        for it in items:
            var_id = str(it.get("variante_id") or "").strip()
            if not var_id:
                raise Exception("Variante inválida en reserva offline")
            try:
                UUID(var_id)
            except (ValueError, TypeError):
                raise Exception(f"Identificador de variante inválido: {var_id}")
            cant = int(it.get("cantidad", 1))
            if cant <= 0:
                raise Exception(f"Cantidad inválida para variante {var_id}")
            cantidades[var_id] = cantidades.get(var_id, 0) + cant

        # Verificar stock disponible en orden determinístico (el trigger fn_actualizar_stock_reservado
        # incrementa stock_reservado al insertar reserva_detalle)
        for var_id in sorted(cantidades.keys()):
            cant = cantidades[var_id]
            stock = await conn.fetchrow(
                """
                SELECT stock_disponible FROM inventario
                WHERE empresa_id = $1 AND sucursal_id = $2 AND variante_id = $3
                FOR UPDATE
                """,
                empresa_id, sucursal_id, var_id
            )
            if not stock or int(stock["stock_disponible"]) < cant:
                raise Exception(f"Stock insuficiente en servidor para variante {var_id}")

        fv_raw = str(p.get("fecha_visita") or datetime.now(timezone.utc).isoformat())
        fv = datetime.fromisoformat(fv_raw.replace("Z", "+00:00"))
        if fv.tzinfo is None:
            fv = fv.replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        expira_en = max(fv, now_utc) + timedelta(hours=2)
        probador = p.get("probador", True)

        reserva_id = await conn.fetchval(
            """
            INSERT INTO reserva (
                id, empresa_id, usuario_id, sucursal_id, estado,
                fecha_visita, expira_en, probador, codigo
            ) VALUES ($1, $2, $3, $4, 'pendiente_preparacion', $5, $6, $7, $8)
            RETURNING id
            """,
            op_id, empresa_id, op_usuario_id, sucursal_id,
            fv,
            expira_en,
            "Cabina 1" if probador else None,
            f"RES-OFF-{str(op_id)[:6].upper()}"
        )

        for var_id, cant in cantidades.items():
            await conn.execute(
                """
                INSERT INTO reserva_detalle (empresa_id, reserva_id, variante_id, cantidad)
                VALUES ($1, $2, $3, $4)
                """,
                empresa_id, reserva_id, var_id, cant
            )

    async def _procesar_cambio_offline_sync(self, conn, empresa_id: str, usuario_id: str, op):
        p = _op_get(op, "payload") or {}
        if isinstance(p, str):
            p = json.loads(p)
        await self.procesar_nota_cambio(
            empresa_id, usuario_id, NotaCambioCreate(
                sucursal_id=_op_get(op, "sucursal_id"),
                venta_origen_id=p.get("venta_origen_id"),
                variante_devuelta_id=p["variante_devuelta_id"],
                variante_nueva_id=p["variante_nueva_id"],
                cantidad=int(p.get("cantidad", 1)),
                motivo=p.get("motivo", "Cambio offline"),
                qr_firma=p.get("qr_firma")
            )
        )

    # =========================================================================
    # CU-32: Resolución de Conflictos (Políticas y Manual)
    # =========================================================================
    async def listar_conflictos(self, empresa_id: str, sucursal_id: Optional[str] = None) -> List[dict]:
        async with self.pool.acquire() as conn:
            query = """
                SELECT op.id, op.empresa_id, op.sucursal_id, s.nombre as sucursal_nombre,
                       op.tipo, op.payload, op.estado, op.ultimo_error, op.creada_en
                FROM operacion_pendiente op
                LEFT JOIN sucursal s ON s.id = op.sucursal_id
                WHERE op.empresa_id = $1 AND op.estado = 'conflicto'
            """
            params = [empresa_id]
            if sucursal_id:
                query += " AND op.sucursal_id = $2"
                params.append(sucursal_id)
            query += " ORDER BY op.creada_en ASC"  # FIFO

            rows = await conn.fetch(query, *params)
            res = []
            for r in rows:
                item = dict(r)
                item["id"] = str(item["id"])
                item["empresa_id"] = str(item["empresa_id"])
                item["sucursal_id"] = str(item["sucursal_id"])
                if isinstance(item["payload"], str):
                    item["payload"] = json.loads(item["payload"])
                res.append(item)
            return res

    async def resolver_conflicto(
        self, empresa_id: str, usuario_id: str, datos: ResolucionConflictoRequest
    ) -> dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                op = await conn.fetchrow(
                    """
                    SELECT * FROM operacion_pendiente
                    WHERE id = $1 AND empresa_id = $2 AND estado = 'conflicto'
                    FOR UPDATE
                    """,
                    datos.operacion_id, empresa_id
                )
                if not op:
                    raise HTTPException(status_code=404, detail="Operación en conflicto no encontrada")

                p = json.loads(op["payload"]) if isinstance(op["payload"], str) else (op["payload"] or {})
                op_tipo = _op_get(op, "tipo") or "venta_offline"
                op_usuario_id = str(_op_get(op, "usuario_id") or usuario_id)
        try:
            UUID(op_usuario_id)
        except (ValueError, TypeError):
            op_usuario_id = str(usuario_id)

                if datos.decision == "ajustar":
                    # Inyectar stock de regularización y reprocesar según tipo
                    items_ajuste = (
                        p.get("items", [])
                        if op_tipo == "reserva_offline"
                        else (
                            [{"variante_id": p["variante_nueva_id"], "cantidad": int(p.get("cantidad", 1))}]
                            if op_tipo == "cambio_offline" and p.get("variante_nueva_id")
                            else p.get("lineas", [])
                        )
                    )
                    for item in items_ajuste:
                        var_id = item["variante_id"]
                        cant = int(item.get("cantidad", 1))
                        await conn.execute(
                            """
                            INSERT INTO inventario (
                                empresa_id, sucursal_id, variante_id,
                                stock_fisico, stock_minimo, actualizado_en
                            ) VALUES ($1, $2, $3, $4, 2, NOW())
                            ON CONFLICT (empresa_id, variante_id, sucursal_id)
                            DO UPDATE SET stock_fisico = inventario.stock_fisico + $4,
                                          actualizado_en = NOW()
                            """,
                            empresa_id, op["sucursal_id"], var_id, cant
                        )
                    if op_tipo == "reserva_offline":
                        await self._procesar_reserva_offline_sync(conn, empresa_id, op_usuario_id, op)
                    elif op_tipo == "cambio_offline":
                        await self._procesar_cambio_offline_sync(conn, empresa_id, op_usuario_id, op)
                    else:
                        await self._procesar_venta_offline_sync(conn, empresa_id, op_usuario_id, op)
                    nuevo_estado = "resuelta"

                elif datos.decision == "rechazar":
                    nuevo_estado = "rechazada"

                elif datos.decision == "aceptar":
                    # Forzar registro según tipo de operación
                    if op_tipo == "reserva_offline":
                        await self._procesar_reserva_offline_sync(conn, empresa_id, op_usuario_id, op)
                    elif op_tipo == "cambio_offline":
                        await self._procesar_cambio_offline_sync(conn, empresa_id, op_usuario_id, op)
                    else:
                        await self._procesar_venta_offline_sync(conn, empresa_id, op_usuario_id, op)
                    nuevo_estado = "resuelta"

                else:
                    nuevo_estado = "resuelta"

                # Asentar en resolucion_conflicto
                await conn.execute(
                    """
                    INSERT INTO resolucion_conflicto (
                        empresa_id, operacion_id, tipo, decision, detalle, resuelto_por
                    ) VALUES ($1, $2, 'stock_insuficiente', $3, $4, $5)
                    """,
                    empresa_id, datos.operacion_id, datos.decision,
                    json.dumps({"motivo": datos.motivo, "detalle": datos.detalle}), usuario_id
                )

                # Actualizar operacion_pendiente
                await conn.execute(
                    """
                    UPDATE operacion_pendiente
                    SET estado = $1, procesada_en = NOW()
                    WHERE id = $2 AND empresa_id = $3
                    """,
                    nuevo_estado, datos.operacion_id, empresa_id
                )

                return {
                    "operacion_id": datos.operacion_id,
                    "decision": datos.decision,
                    "nuevo_estado": nuevo_estado,
                    "mensaje": "Conflicto de sincronización resuelto con éxito"
                }

