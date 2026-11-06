import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from asyncpg import Pool
from fastapi import HTTPException

from app.schemas.sync import (
    CatalogoOfflinePackage,
    SoftLockCreate,
    SoftLockResponse,
    NotaCambioCreate,
    SyncBatchRequest,
    SyncBatchResponse,
    ConflictoSyncItem,
    ResolucionConflictoRequest
)

SECRET_KEY_QR = "fashionstore_offline_secret_key_2026"

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
            # 1. Prendas activas
            prendas_rows = await conn.fetch(
                """
                SELECT id, codigo, nombre, descripcion, precio_base, categoria_id, imagen_url
                FROM prenda
                WHERE empresa_id = $1 AND activo = true
                ORDER BY nombre ASC
                """,
                empresa_id
            )
            prendas = [dict(r) for r in prendas_rows]

            # 2. Variantes activas
            variantes_rows = await conn.fetch(
                """
                SELECT v.id, v.prenda_id, v.sku, v.precio_venta, v.codigo_barras,
                       t.nombre as talla, c.nombre as color, c.codigo_hex as color_hex
                FROM variante_prenda v
                LEFT JOIN talla t ON t.id = v.talla_id
                LEFT JOIN color c ON c.id = v.color_id
                WHERE v.empresa_id = $1 AND v.activo = true
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
                v["id"] = str(v["id"])
                v["prenda_id"] = str(v["prenda_id"])
                if v.get("precio_venta"):
                    v["precio_venta"] = float(v["precio_venta"])

            return CatalogoOfflinePackage(
                empresa_id=str(empresa_id),
                sucursal_id=str(sucursal_id) if sucursal_id else None,
                generado_en=datetime.now(timezone.utc),
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
                        resultado = {"status": "confirmada", "op_id": op.id}
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
                            op.id, empresa_id, op.sucursal_id, usuario_id, op.tipo,
                            json.dumps(op.payload), op.idempotency_key
                        )

                        confirmados.append(op.id)
                except Exception as ex:
                    # Registrar en conflicto sin anular el resto del lote
                    err_msg = str(ex)
                    await conn.execute(
                        """
                        INSERT INTO operacion_pendiente (
                            id, empresa_id, sucursal_id, usuario_id, tipo,
                            payload, idempotency_key, estado, ultimo_error
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'conflicto', $8)
                        ON CONFLICT (empresa_id, id) DO UPDATE
                        SET estado = 'conflicto', ultimo_error = $8
                        """,
                        op.id, empresa_id, op.sucursal_id, usuario_id, op.tipo,
                        json.dumps(op.payload), op.idempotency_key, err_msg
                    )
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
        p = op.payload
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
                empresa_id, op.sucursal_id, var_id
            )
            if not stock or stock["stock_disponible"] < cant:
                raise Exception(f"Stock insuficiente en servidor para variante {var_id}")

            # Descontar stock
            await conn.execute(
                """
                UPDATE inventario
                SET stock_fisico = stock_fisico - $1
                WHERE empresa_id = $2 AND sucursal_id = $3 AND variante_id = $4
                """,
                cant, empresa_id, op.sucursal_id, var_id
            )

        # Insertar venta oficial
        total = float(p.get("total", 0.0))
        numero_ticket = f"OFF-{op.id[:8].upper()}"
        venta_id = await conn.fetchval(
            """
            INSERT INTO venta (
                id, empresa_id, sucursal_id, usuario_id, numero,
                subtotal, total, estado, origen, cliente_nombre, cliente_documento
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'completada', 'pos', $8, $9)
            RETURNING id
            """,
            op.id, empresa_id, op.sucursal_id, usuario_id, numero_ticket,
            total / 1.13, total, p.get("cliente_nombre", "Consumidor Final"),
            p.get("cliente_documento", "0")
        )

        for l in lineas:
            cant = int(l["cantidad"])
            pu = float(l["precio_unitario"])
            await conn.execute(
                """
                INSERT INTO detalle_venta (empresa_id, venta_id, variante_id, cantidad, precio_unitario, subtotal)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                empresa_id, venta_id, l["variante_id"], cant, pu, cant * pu
            )

    async def _procesar_reserva_offline_sync(self, conn, empresa_id: str, usuario_id: str, op):
        p = op.payload
        items = p.get("items", [])
        fecha_visita = p.get("fecha_visita") or datetime.now(timezone.utc).isoformat()
        probador = p.get("probador", True)

        reserva_id = await conn.fetchval(
            """
            INSERT INTO reserva (
                id, empresa_id, sucursal_id, estado, fecha_visita, probador, codigo
            ) VALUES ($1, $2, $3, 'pendiente_preparacion', $4, $5, $6)
            RETURNING id
            """,
            op.id, empresa_id, op.sucursal_id,
            datetime.fromisoformat(fecha_visita.replace("Z", "+00:00")),
            "Cabina 1" if probador else None,
            f"RES-OFF-{op.id[:6].upper()}"
        )

        for it in items:
            await conn.execute(
                """
                INSERT INTO detalle_reserva (empresa_id, reserva_id, variante_id, cantidad)
                VALUES ($1, $2, $3, $4)
                """,
                empresa_id, reserva_id, it["variante_id"], int(it.get("cantidad", 1))
            )

    async def _procesar_cambio_offline_sync(self, conn, empresa_id: str, usuario_id: str, op):
        p = op.payload
        await self.procesar_nota_cambio(
            empresa_id, usuario_id, NotaCambioCreate(
                sucursal_id=op.sucursal_id,
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

                p = json.loads(op["payload"]) if isinstance(op["payload"], str) else op["payload"]

                if datos.decision == "ajustar":
                    # Inyectar stock de regularización y asentar la venta
                    for linea in p.get("lineas", []):
                        var_id = linea["variante_id"]
                        cant = int(linea["cantidad"])
                        await conn.execute(
                            """
                            UPDATE inventario
                            SET stock_fisico = stock_fisico + $1
                            WHERE empresa_id = $2 AND sucursal_id = $3 AND variante_id = $4
                            """,
                            cant, empresa_id, op["sucursal_id"], var_id
                        )
                    await self._procesar_venta_offline_sync(conn, empresa_id, usuario_id, op)
                    nuevo_estado = "resuelta"

                elif datos.decision == "rechazar":
                    nuevo_estado = "rechazada"

                elif datos.decision == "aceptar":
                    # Forzar registro
                    await self._procesar_venta_offline_sync(conn, empresa_id, usuario_id, op)
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

