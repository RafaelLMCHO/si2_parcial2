"""
Servicio de Pagos (CU-24).
Integración con pasarela Stripe Sandbox y conciliación por Webhook.
"""
import asyncio
import logging
import os
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, get_pool, tenant_connection

logger = logging.getLogger(__name__)

# Configuración desde entorno
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_test_sample123456789")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PAYMENT_CURRENCY = os.environ.get("PAYMENT_CURRENCY", "usd").lower()

if STRIPE_SECRET_KEY and not STRIPE_SECRET_KEY.startswith("sk_test_"):
    logger.warning("ALERTA: STRIPE_SECRET_KEY no tiene prefijo 'sk_test_'. Verifique que está en modo Sandbox.")


# ---------------------------------------------------------------------------
# Patrón Adapter / Puerto para Pasarela de Pago
# ---------------------------------------------------------------------------
class PasarelaPago:
    async def crear_intencion(
        self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str
    ) -> dict:
        """Crea PaymentIntent y retorna {'id': intent_id, 'client_secret': secret}"""
        raise NotImplementedError

    async def reembolsar(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        """Emite un reembolso y retorna {'id': refund_id}"""
        raise NotImplementedError


class StripeGateway(PasarelaPago):
    def __init__(self):
        try:
            import stripe
            self.stripe = stripe
            self.stripe.api_key = STRIPE_SECRET_KEY
        except ImportError:
            logger.warning("Paquete 'stripe' no disponible. Usando fallback simulado.")
            self.stripe = None

    async def crear_intencion(
        self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str
    ) -> dict:
        if not self.stripe:
            return MockGateway().crear_intencion_sync(monto_centavos, moneda, metadata, idempotency_key)

        loop = asyncio.get_event_loop()
        intent = await loop.run_in_executor(
            None,
            lambda: self.stripe.PaymentIntent.create(
                amount=monto_centavos,
                currency=moneda,
                metadata=metadata,
                idempotency_key=idempotency_key,
            ),
        )
        return {"id": intent.id, "client_secret": intent.client_secret}

    async def reembolsar(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        if not self.stripe:
            return MockGateway().reembolsar_sync(pasarela_id, monto_centavos)

        loop = asyncio.get_event_loop()
        args = {"payment_intent": pasarela_id}
        if monto_centavos:
            args["amount"] = monto_centavos
        refund = await loop.run_in_executor(
            None,
            lambda: self.stripe.Refund.create(**args),
        )
        return {"id": refund.id}


class MockGateway(PasarelaPago):
    """Pasarela de pruebas sin conexión a Stripe."""
    def crear_intencion_sync(self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str) -> dict:
        clean_key = idempotency_key.replace("-", "")[:12]
        intent_id = f"pi_mock_{clean_key}"
        return {
            "id": intent_id,
            "client_secret": f"{intent_id}_secret_mock",
        }

    async def crear_intencion(
        self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str
    ) -> dict:
        return self.crear_intencion_sync(monto_centavos, moneda, metadata, idempotency_key)

    def reembolsar_sync(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        return {"id": f"re_mock_{pasarela_id}"}

    async def reembolsar(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        return self.reembolsar_sync(pasarela_id, monto_centavos)


def get_gateway() -> PasarelaPago:
    if STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.startswith("sk_test_"):
        return StripeGateway()
    return MockGateway()


# ---------------------------------------------------------------------------
# Operaciones de Pago
# ---------------------------------------------------------------------------

async def crear_intencion_pago(
    empresa_id: str,
    user_id: str,
    rol: str,
    venta_id: str,
    idempotency_key: str,
    ip: Optional[str] = None,
) -> dict:
    """
    Crea o reutiliza un pago pendiente y genera una intención de cobro en Stripe.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        venta = await conn.fetchrow(
            """
            SELECT id, empresa_id, usuario_id, total, estado, moneda
              FROM venta
             WHERE id = $1 AND empresa_id = $2
            """,
            UUID(venta_id),
            UUID(empresa_id),
        )
        if venta is None:
            raise api_error(404, "VENTA_NO_ENCONTRADA", "La venta especificada no existe")

        # Clientes solo pueden pagar sus ventas
        if rol == "cliente" and str(venta["usuario_id"]) != user_id:
            raise api_error(403, "PERMISO_DENEGADO", "No puedes realizar el pago de una orden ajena")

        if venta["estado"] not in ("pendiente_pago", "pago_fallido"):
            raise api_error(
                409,
                "ESTADO_INVALIDO",
                f"La venta no admite pago en su estado actual ({venta['estado']})",
            )

        monto_total = Decimal(str(venta["total"]))
        if monto_total <= 0:
            raise api_error(400, "MONTO_INVALIDO", "El total de la orden debe ser mayor a 0")

        # Conversión a centavos
        # Si la moneda de Stripe es USD y la venta es BOB, se documenta que en sandbox se usa USD directo o paridad 1:1 simulada
        monto_centavos = int(monto_total * 100)

        # Buscar si ya existe un pago pendiente con esta clave o para esta venta
        pago_existente = await conn.fetchrow(
            """
            SELECT id, pasarela_id, estado, monto, idempotency_key
              FROM pago
             WHERE venta_id = $1 AND empresa_id = $2 AND estado = 'pendiente'
             ORDER BY created_at DESC
             LIMIT 1
            """,
            UUID(venta_id),
            UUID(empresa_id),
        )

        pago_id = None
        if pago_existente:
            pago_id = pago_existente["id"]
        else:
            # Crear registro de pago pendiente
            pago_row = await conn.fetchrow(
                """
                INSERT INTO pago (
                    empresa_id, venta_id, monto, moneda, metodo, idempotency_key, estado
                )
                VALUES ($1, $2, $3, $4, 'tarjeta', $5, 'pendiente')
                ON CONFLICT (empresa_id, idempotency_key)
                DO UPDATE SET idempotency_key = EXCLUDED.idempotency_key
                RETURNING id
                """,
                UUID(empresa_id),
                UUID(venta_id),
                monto_total,
                PAYMENT_CURRENCY.upper(),
                idempotency_key,
            )
            pago_id = pago_row["id"]

        # Invocar la pasarela
        gateway = get_gateway()
        metadata = {
            "empresa_id": str(empresa_id),
            "venta_id": str(venta_id),
            "pago_id": str(pago_id),
            "usuario_id": str(user_id),
        }

        try:
            intent_res = await gateway.crear_intencion(
                monto_centavos=monto_centavos,
                moneda=PAYMENT_CURRENCY,
                metadata=metadata,
                idempotency_key=f"{idempotency_key}_{pago_id}",
            )
        except Exception as e:
            logger.error("Error al crear PaymentIntent con pasarela: %s", str(e))
            raise api_error(502, "ERROR_PASARELA", f"Error de comunicación con Stripe: {str(e)}")

        pasarela_id = intent_res["id"]
        client_secret = intent_res.get("client_secret", "")

        # Asociar pasarela_id al registro pago
        await conn.execute(
            """
            UPDATE pago
               SET pasarela_id = $1
             WHERE id = $2 AND empresa_id = $3
            """,
            pasarela_id,
            pago_id,
            UUID(empresa_id),
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="pago",
        entidad_id=str(pago_id),
        datos_despues={"pasarela_id": pasarela_id, "monto": str(monto_total), "moneda": PAYMENT_CURRENCY},
        ip=ip,
    )

    return {
        "pago_id": str(pago_id),
        "client_secret": client_secret,
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "monto": monto_centavos,
        "moneda": PAYMENT_CURRENCY,
    }


async def procesar_webhook_stripe(payload_bytes: bytes, signature: Optional[str]) -> dict:
    """
    Procesa un webhook emitido por Stripe.
    Valida firma criptográfica, aplica idempotencia y finaliza la venta.
    """
    event = None
    event_id = None
    event_type = None

    if STRIPE_WEBHOOK_SECRET and signature:
        try:
            import stripe
            event = stripe.Webhook.construct_event(
                payload=payload_bytes,
                sig_header=signature,
                secret=STRIPE_WEBHOOK_SECRET,
            )
            event_id = event["id"]
            event_type = event["type"]
        except Exception as exc:
            logger.warning("Firma de webhook Stripe inválida: %s", str(exc))
            raise api_error(400, "FIRMA_INVALIDA", f"Firma criptográfica no válida: {str(exc)}")
    else:
        # En modo sandbox o prueba local sin secret configurado, parsear payload JSON
        import json
        try:
            event = json.loads(payload_bytes.decode("utf-8"))
            event_id = event.get("id")
            event_type = event.get("type")
        except Exception as exc:
            raise api_error(400, "PAYLOAD_INVALIDO", f"JSON mal formado: {str(exc)}")

    if not event_id or not event_type:
        raise api_error(400, "EVENTO_INVALIDO", "Faltan campos id o type en el webhook")

    pool = get_pool()

    # Idempotencia de webhooks (tabla stripe_evento)
    async with pool.acquire() as conn:
        ya_procesado = await conn.fetchval(
            "SELECT id FROM stripe_evento WHERE id = $1", event_id
        )
        if ya_procesado:
            return {"status": "already_processed", "event_id": event_id}

        await conn.execute(
            """
            INSERT INTO stripe_evento (id, tipo, procesado_en)
            VALUES ($1, $2, now())
            ON CONFLICT (id) DO NOTHING
            """,
            event_id,
            event_type,
        )

    # Extraer data del objeto
    data_object = event.get("data", {}).get("object", {})
    metadata = data_object.get("metadata", {})
    empresa_id_str = metadata.get("empresa_id")
    venta_id_str = metadata.get("venta_id")
    pago_id_str = metadata.get("pago_id")

    if not empresa_id_str or not venta_id_str:
        logger.warning("Evento %s no contiene empresa_id o venta_id en metadata. Ignorando conciliación.", event_id)
        return {"status": "ignored", "reason": "no_metadata"}

    empresa_id = UUID(empresa_id_str)
    venta_id = UUID(venta_id_str)

    if event_type == "payment_intent.succeeded":
        charge_id = None
        charges = data_object.get("charges", {}).get("data", [])
        if charges:
            charge_id = charges[0].get("id")
        else:
            charge_id = data_object.get("latest_charge") or event_id

        async with pool.acquire() as conn:
            async with conn.transaction():
                # Actualizar pago a completado
                if pago_id_str:
                    await conn.execute(
                        """
                        UPDATE pago
                           SET estado = 'completado',
                               referencia = $1,
                               pagado_en = now()
                         WHERE id = $2 AND empresa_id = $3
                        """,
                        str(charge_id),
                        UUID(pago_id_str),
                        empresa_id,
                    )
                else:
                    await conn.execute(
                        """
                        UPDATE pago
                           SET estado = 'completado',
                               referencia = $1,
                               pagado_en = now()
                         WHERE venta_id = $2 AND empresa_id = $3 AND estado = 'pendiente'
                        """,
                        str(charge_id),
                        venta_id,
                        empresa_id,
                    )

        # Invocar la finalización de la venta con regularización de stock (CU-22)
        from app.services import checkout_service
        try:
            await checkout_service.finalizar_venta_pagada(
                empresa_id=str(empresa_id),
                venta_id=str(venta_id),
                pago_id=pago_id_str,
                ip=None,
            )
        except Exception as e:
            logger.error("Error al finalizar venta tras webhook exitoso: %s", str(e))
            raise api_error(500, "ERROR_FINALIZACION", f"Error al regularizar inventario: {str(e)}")

        await audit_event(
            empresa_id=str(empresa_id),
            usuario_id=None,
            actor_tipo="sistema",
            accion="update",
            entidad="pago",
            entidad_id=pago_id_str,
            datos_despues={"evento": event_type, "venta_id": str(venta_id), "referencia": charge_id},
        )

    elif event_type == "payment_intent.payment_failed":
        last_error = data_object.get("last_payment_error", {})
        decline_code = last_error.get("decline_code") or last_error.get("code") or "tarjeta_rechazada"
        error_msg = last_error.get("message") or "El pago fue rechazado por la entidad bancaria"

        async with pool.acquire() as conn:
            async with conn.transaction():
                if pago_id_str:
                    await conn.execute(
                        """
                        UPDATE pago
                           SET estado = 'fallido',
                               referencia = $1
                         WHERE id = $2 AND empresa_id = $3
                        """,
                        f"{decline_code}: {error_msg}"[:100],
                        UUID(pago_id_str),
                        empresa_id,
                    )

                # Marcar venta en pago_fallido sin tocar inventario
                await conn.execute(
                    """
                    UPDATE venta
                       SET estado = 'pago_fallido',
                           updated_at = now()
                     WHERE id = $1 AND empresa_id = $2
                    """,
                    venta_id,
                    empresa_id,
                )

                await conn.execute(
                    """
                    INSERT INTO venta_estado_historial (
                        empresa_id, venta_id, estado_anterior, estado_nuevo, motivo
                    )
                    VALUES ($1, $2, 'pendiente_pago', 'pago_fallido', $3)
                    """,
                    empresa_id,
                    venta_id,
                    f"Rechazo de pasarela: {decline_code}",
                )

        await audit_event(
            empresa_id=str(empresa_id),
            usuario_id=None,
            actor_tipo="sistema",
            accion="update",
            entidad="venta",
            entidad_id=str(venta_id),
            datos_despues={"estado": "pago_fallido", "motivo": decline_code},
        )

    elif event_type == "charge.refunded":
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE pago
                   SET estado = 'reembolsado'
                 WHERE venta_id = $1 AND empresa_id = $2
                """,
                venta_id,
                empresa_id,
            )

    return {"status": "success", "event_type": event_type, "event_id": event_id}


async def get_pago(empresa_id: str, user_id: str, rol: str, pago_id: str) -> dict:
    """Consulta detalles de un pago."""
    async with tenant_connection(empresa_id, user_id) as conn:
        pago = await conn.fetchrow(
            """
            SELECT p.id, p.venta_id, p.monto, p.metodo, p.estado,
                   p.pasarela_id, p.referencia, p.created_at,
                   v.usuario_id AS venta_usuario_id
              FROM pago p
              JOIN venta v ON v.id = p.venta_id
             WHERE p.id = $1 AND p.empresa_id = $2
            """,
            UUID(pago_id),
            UUID(empresa_id),
        )
        if not pago:
            raise api_error(404, "PAGO_NO_ENCONTRADO", "El registro de pago no existe")

        if rol == "cliente" and str(pago["venta_usuario_id"]) != user_id:
            raise api_error(403, "PERMISO_DENEGADO", "No puedes ver pagos de otras órdenes")

        return {
            "id": str(pago["id"]),
            "venta_id": str(pago["venta_id"]),
            "monto": pago["monto"],
            "metodo": pago["metodo"],
            "estado": pago["estado"],
            "pasarela_id": pago["pasarela_id"],
            "referencia": pago["referencia"],
            "created_at": pago["created_at"],
        }


async def get_estado_pago(empresa_id: str, user_id: str, rol: str, venta_id: str) -> dict:
    """Polling del frontend para verificar el estado de la venta y pago asociado."""
    async with tenant_connection(empresa_id, user_id) as conn:
        venta = await conn.fetchrow(
            """
            SELECT v.id, v.estado, v.usuario_id
              FROM venta v
             WHERE v.id = $1 AND v.empresa_id = $2
            """,
            UUID(venta_id),
            UUID(empresa_id),
        )
        if not venta:
            raise api_error(404, "VENTA_NO_ENCONTRADA", "Venta no encontrada")

        if rol == "cliente" and str(venta["usuario_id"]) != user_id:
            raise api_error(403, "PERMISO_DENEGADO", "No puedes consultar el estado de esta venta")

        pago = await conn.fetchrow(
            """
            SELECT id, estado, pasarela_id, referencia
              FROM pago
             WHERE venta_id = $1 AND empresa_id = $2
             ORDER BY created_at DESC
             LIMIT 1
            """,
            UUID(venta_id),
            UUID(empresa_id),
        )

        mensaje_error = None
        if pago and pago["estado"] == "fallido":
            mensaje_error = pago.get("referencia") or "El pago fue rechazado"

        return {
            "venta_id": str(venta["id"]),
            "venta_estado": venta["estado"],
            "pago_id": str(pago["id"]) if pago else None,
            "pago_estado": pago["estado"] if pago else None,
            "pasarela_id": pago["pasarela_id"] if pago else None,
            "mensaje_error": mensaje_error,
        }


async def reembolsar_pago(empresa_id: str, pago_id: str, motivo: Optional[str] = None) -> dict:
    """Emite un reembolso en pasarela y concilia en base de datos."""
    async with tenant_connection(empresa_id) as conn:
        pago = await conn.fetchrow(
            """
            SELECT id, pasarela_id, monto, estado
              FROM pago
             WHERE id = $1 AND empresa_id = $2
            """,
            UUID(pago_id),
            UUID(empresa_id),
        )
        if not pago:
            raise api_error(404, "PAGO_NO_ENCONTRADO", "Pago no encontrado")

        if pago["estado"] != "completado":
            raise api_error(409, "ESTADO_INVALIDO", f"Solo se pueden reembolsar pagos completados (estado: {pago['estado']})")

        pasarela_id = pago["pasarela_id"]
        if pasarela_id:
            gateway = get_gateway()
            monto_centavos = int(Decimal(str(pago["monto"])) * 100)
            try:
                await gateway.reembolsar(pasarela_id, monto_centavos)
            except Exception as exc:
                logger.error("Error al emitir reembolso en pasarela: %s", str(exc))

        await conn.execute(
            """
            UPDATE pago
               SET estado = 'reembolsado',
                   referencia = COALESCE(referencia, '') || ' [Reembolsado: ' || $1 || ']'
             WHERE id = $2 AND empresa_id = $3
            """,
            motivo or "Reembolso automático",
            UUID(pago_id),
            UUID(empresa_id),
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=None,
        actor_tipo="sistema",
        accion="update",
        entidad="pago",
        entidad_id=pago_id,
        datos_despues={"estado": "reembolsado", "motivo": motivo},
    )

    return {"ok": True, "pago_id": pago_id, "estado": "reembolsado"}



class PagoService:
    def __init__(self, pool=None):
        self.pool = pool

    async def crear_intencion_pago(self, empresa_id: str, datos=None):
        return await crear_intencion_pago(empresa_id=empresa_id, req=datos)

    async def consultar_pago(self, empresa_id: str, pago_id: str):
        return await get_pago(empresa_id=empresa_id, pago_id=pago_id)

    async def solicitar_reembolso(self, empresa_id: str, pago_id: str, datos=None):
        return await reembolsar_pago(empresa_id=empresa_id, pago_id=pago_id, req=datos)
