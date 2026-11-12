"""
Servicio de Pagos (CU-24).
Integración con pasarela Stripe Sandbox y conciliación por Webhook.
"""
import asyncio
import json
import logging
import os
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.config import get_settings
from app.core.errors import api_error
from app.db import audit_event, get_pool, tenant_connection

logger = logging.getLogger(__name__)

# Referencias de entorno para compatibilidad con tests/monkeypatch
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PAYMENT_CURRENCY = os.environ.get("PAYMENT_CURRENCY", "")


def _cfg(env_key: str, module_val: str, setting_attr: str, default: str = "") -> str:
    if env_key in os.environ and os.environ[env_key] != "":
        return os.environ[env_key].strip()
    if module_val:
        return module_val.strip()
    val = getattr(get_settings(), setting_attr, "") or ""
    return val.strip() or default


def _get_stripe_secret_key() -> str:
    return _cfg("STRIPE_SECRET_KEY", STRIPE_SECRET_KEY, "stripe_secret_key", "")


def _get_stripe_publishable_key() -> str:
    return _cfg(
        "STRIPE_PUBLISHABLE_KEY",
        STRIPE_PUBLISHABLE_KEY,
        "stripe_publishable_key",
        "pk_test_sample123456789",
    )


def _get_stripe_webhook_secret() -> str:
    return _cfg("STRIPE_WEBHOOK_SECRET", STRIPE_WEBHOOK_SECRET, "stripe_webhook_secret", "")


def _get_payment_currency() -> str:
    return _cfg("PAYMENT_CURRENCY", PAYMENT_CURRENCY, "payment_currency", "usd").lower()


# ---------------------------------------------------------------------------
# Patrón Adapter / Puerto para Pasarela de Pago
# ---------------------------------------------------------------------------
class PasarelaPago:
    async def crear_intencion(
        self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str
    ) -> dict:
        """Crea PaymentIntent y retorna {'id': intent_id, 'client_secret': secret}"""
        raise NotImplementedError

    async def consultar_intencion(self, pasarela_id: str) -> dict:
        """Recupera un PaymentIntent en Stripe para conciliación."""
        raise NotImplementedError

    async def confirmar_intencion(self, pasarela_id: str, payment_method: Optional[str] = None) -> dict:
        """Confirma un PaymentIntent existente."""
        raise NotImplementedError

    async def reembolsar(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        """Emite un reembolso y retorna {'id': refund_id}"""
        raise NotImplementedError


class StripeGateway(PasarelaPago):
    def __init__(self, api_key: Optional[str] = None):
        import stripe

        self.stripe = stripe
        self.stripe.api_key = api_key or _get_stripe_secret_key()

    async def crear_intencion(
        self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str
    ) -> dict:
        intent = await asyncio.to_thread(
            self.stripe.PaymentIntent.create,
            amount=monto_centavos,
            currency=moneda,
            metadata=metadata,
            idempotency_key=idempotency_key,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )
        return {
            "id": intent.id,
            "client_secret": intent.client_secret,
            "status": getattr(intent, "status", "requires_payment_method"),
        }

    async def consultar_intencion(self, pasarela_id: str) -> dict:
        intent = await asyncio.to_thread(
            self.stripe.PaymentIntent.retrieve,
            pasarela_id,
        )
        return {
            "id": intent.id,
            "status": getattr(intent, "status", "unknown"),
            "latest_charge": getattr(intent, "latest_charge", None),
            "metadata": getattr(intent, "metadata", {}) or {},
        }

    async def confirmar_intencion(self, pasarela_id: str, payment_method: Optional[str] = None) -> dict:
        kwargs = {}
        if payment_method:
            kwargs["payment_method"] = payment_method
        intent = await asyncio.to_thread(
            self.stripe.PaymentIntent.confirm,
            pasarela_id,
            **kwargs,
        )
        return {
            "id": intent.id,
            "status": getattr(intent, "status", "unknown"),
            "latest_charge": getattr(intent, "latest_charge", None),
        }

    async def reembolsar(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        args = {"payment_intent": pasarela_id}
        if monto_centavos is not None:
            args["amount"] = monto_centavos
        refund = await asyncio.to_thread(self.stripe.Refund.create, **args)
        return {"id": refund.id, "status": getattr(refund, "status", "succeeded")}


class MockGateway(PasarelaPago):
    """Pasarela simulada exclusivamente para suite de tests sin claves Stripe."""

    def crear_intencion_sync(self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str) -> dict:
        clean_key = idempotency_key.replace("-", "")[:12]
        intent_id = f"pi_mock_{clean_key}"
        return {
            "id": intent_id,
            "client_secret": f"{intent_id}_secret_mock",
            "status": "requires_payment_method",
        }

    async def crear_intencion(
        self, monto_centavos: int, moneda: str, metadata: dict, idempotency_key: str
    ) -> dict:
        return self.crear_intencion_sync(monto_centavos, moneda, metadata, idempotency_key)

    async def consultar_intencion(self, pasarela_id: str) -> dict:
        return {"id": pasarela_id, "status": "succeeded", "latest_charge": f"ch_mock_{pasarela_id[:10]}"}

    async def confirmar_intencion(self, pasarela_id: str, payment_method: Optional[str] = None) -> dict:
        return {"id": pasarela_id, "status": "succeeded", "latest_charge": f"ch_mock_{pasarela_id[:10]}"}

    def reembolsar_sync(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        return {"id": f"re_mock_{pasarela_id}", "status": "succeeded"}

    async def reembolsar(self, pasarela_id: str, monto_centavos: Optional[int] = None) -> dict:
        return self.reembolsar_sync(pasarela_id, monto_centavos)


def get_gateway() -> PasarelaPago:
    secret_key = _get_stripe_secret_key()
    if secret_key:
        if not secret_key.startswith("sk_test_"):
            logger.warning("ALERTA: STRIPE_SECRET_KEY no tiene prefijo 'sk_test_'. Verifique modo Sandbox.")
        return StripeGateway(api_key=secret_key)

    if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("STRIPE_ALLOW_MOCK", "").lower() == "true":
        return MockGateway()

    raise api_error(
        503,
        "PASARELA_NO_CONFIGURADA",
        "La pasarela de pagos Stripe no está configurada (STRIPE_SECRET_KEY vacía).",
    )


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

        currency = _get_payment_currency()
        publishable_key = _get_stripe_publishable_key()

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
                currency.upper(),
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
                moneda=currency,
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
        datos_despues={"pasarela_id": pasarela_id, "monto": str(monto_total), "moneda": currency},
        ip=ip,
    )

    return {
        "pago_id": str(pago_id),
        "client_secret": client_secret,
        "publishable_key": publishable_key,
        "monto": monto_centavos,
        "moneda": currency,
    }


async def procesar_webhook_stripe(payload_bytes: bytes, signature: Optional[str]) -> dict:
    """
    Procesa un webhook emitido por Stripe.
    Valida firma criptográfica si STRIPE_WEBHOOK_SECRET está configurada,
    aplica idempotencia y finaliza la venta.
    """
    event = None
    event_id = None
    event_type = None
    webhook_secret = _get_stripe_webhook_secret()

    if webhook_secret:
        if not signature:
            raise api_error(
                400,
                "FIRMA_REQUERIDA",
                "Cabecera Stripe-Signature requerida para verificar webhook",
            )
        try:
            import stripe
            event = stripe.Webhook.construct_event(
                payload=payload_bytes,
                sig_header=signature,
                secret=webhook_secret,
            )
            event_id = event["id"]
            event_type = event["type"]
        except Exception as exc:
            logger.warning("Firma de webhook Stripe inválida: %s", str(exc))
            raise api_error(400, "FIRMA_INVALIDA", f"Firma criptográfica no válida: {str(exc)}")
    else:
        if "PYTEST_CURRENT_TEST" not in os.environ and os.environ.get("STRIPE_ALLOW_MOCK", "").lower() != "true":
            logger.warning("Webhook Stripe recibido sin STRIPE_WEBHOOK_SECRET configurado en entorno.")
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
            mensaje_error = pago["referencia"] or "El pago fue rechazado"

        return {
            "venta_id": str(venta["id"]),
            "venta_estado": venta["estado"],
            "pago_id": str(pago["id"]) if pago else None,
            "pago_estado": pago["estado"] if pago else None,
            "pasarela_id": pago["pasarela_id"] if pago else None,
            "mensaje_error": mensaje_error,
        }


async def listar_pagos(
    empresa_id: str,
    user_id: str,
    rol: str,
    estado: Optional[str] = None,
    venta_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Lista pagos del tenant (clientes solo ven pagos de sus propias ventas)."""
    offset = (page - 1) * page_size
    conditions = ["p.empresa_id = $1"]
    params: list = [UUID(empresa_id)]

    if rol == "cliente":
        params.append(UUID(user_id))
        conditions.append(f"v.usuario_id = ${len(params)}")
    if estado:
        params.append(estado.strip().lower())
        conditions.append(f"p.estado = ${len(params)}")
    if venta_id:
        params.append(UUID(venta_id))
        conditions.append(f"p.venta_id = ${len(params)}")

    where = " AND ".join(conditions)

    async with tenant_connection(empresa_id, user_id) as conn:
        total = int(
            await conn.fetchval(
                f"SELECT count(*)::int FROM pago p JOIN venta v ON v.id = p.venta_id WHERE {where}",
                *params,
            )
            or 0
        )
        params_q = [*params, page_size, offset]
        rows = await conn.fetch(
            f"""
            SELECT p.id, p.venta_id, p.monto, p.metodo, p.estado,
                   p.pasarela_id, p.referencia, p.created_at
              FROM pago p
              JOIN venta v ON v.id = p.venta_id
             WHERE {where}
             ORDER BY p.created_at DESC
             LIMIT ${len(params_q) - 1} OFFSET ${len(params_q)}
            """,
            *params_q,
        )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(r["id"]),
                "venta_id": str(r["venta_id"]),
                "monto": float(r["monto"]),
                "metodo": r["metodo"],
                "estado": r["estado"],
                "pasarela_id": r["pasarela_id"],
                "referencia": r["referencia"],
                "created_at": r["created_at"],
            }
            for r in rows
        ],
    }


async def conciliar_pago(
    empresa_id: str,
    user_id: str,
    rol: str,
    pago_id: str,
    confirmar_payment_method: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    """
    CU-24: Consulta o confirma un PaymentIntent directamente en Stripe y concilia
    el estado del pago y la venta en BD.
    """
    async with tenant_connection(empresa_id, user_id) as conn:
        pago = await conn.fetchrow(
            """
            SELECT p.id, p.venta_id, p.pasarela_id, p.estado, p.referencia,
                   v.usuario_id AS venta_usuario_id, v.estado AS venta_estado
              FROM pago p
              JOIN venta v ON v.id = p.venta_id
             WHERE p.id = $1 AND p.empresa_id = $2
             FOR UPDATE OF p
            """,
            UUID(pago_id),
            UUID(empresa_id),
        )
        if not pago:
            raise api_error(404, "PAGO_NO_ENCONTRADO", "Pago no encontrado")
        if rol == "cliente" and str(pago["venta_usuario_id"]) != user_id:
            raise api_error(403, "PERMISO_DENEGADO", "No puedes conciliar pagos de otras órdenes")
        if not pago["pasarela_id"]:
            raise api_error(409, "SIN_PASARELA_ID", "El pago no tiene un PaymentIntent asociado en pasarela")

        gateway = get_gateway()
        try:
            if confirmar_payment_method:
                pi = await gateway.confirmar_intencion(pago["pasarela_id"], confirmar_payment_method)
            else:
                pi = await gateway.consultar_intencion(pago["pasarela_id"])
        except Exception as exc:
            raise api_error(502, "ERROR_PASARELA", f"Error consultando pasarela: {exc}")

        pi_status = pi.get("status")
        referencia = pi.get("latest_charge") or pago["pasarela_id"]

        if pi_status == "succeeded" and pago["estado"] != "completado":
            await conn.execute(
                """
                UPDATE pago
                   SET estado = 'completado',
                       referencia = COALESCE(referencia, $1),
                       pagado_en = now()
                 WHERE id = $2 AND empresa_id = $3
                """,
                str(referencia)[:100],
                UUID(pago_id),
                UUID(empresa_id),
            )

    if pi_status == "succeeded" and pago["venta_estado"] in ("pendiente_pago", "pago_fallido"):
        from app.services import checkout_service
        await checkout_service.finalizar_venta_pagada(
            empresa_id=str(empresa_id),
            venta_id=str(pago["venta_id"]),
            pago_id=str(pago_id),
            ip=ip,
        )

    return await get_estado_pago(empresa_id=empresa_id, user_id=user_id, rol=rol, venta_id=str(pago["venta_id"]))


async def reembolsar_pago(
    empresa_id: str,
    pago_id: str,
    *,
    user_id: Optional[str] = None,
    rol: str = "administrador",
    monto: Optional[float] = None,
    motivo: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    """CU-24: Emite un reembolso total o parcial en pasarela y actualiza pago + venta."""
    if rol not in {"superadmin", "administrador", "cajero"}:
        raise api_error(
            403,
            "PERMISO_DENEGADO",
            "Solo superadmin, administrador o cajero pueden procesar reembolsos",
        )

    motivo_final = (motivo or "Reembolso emitido desde sistema").strip()

    async with tenant_connection(empresa_id, user_id) as conn:
        pago = await conn.fetchrow(
            """
            SELECT p.id, p.venta_id, p.pasarela_id, p.monto, p.estado, p.referencia,
                   v.estado AS venta_estado
              FROM pago p
              JOIN venta v ON v.id = p.venta_id
             WHERE p.id = $1 AND p.empresa_id = $2
             FOR UPDATE OF p
            """,
            UUID(pago_id),
            UUID(empresa_id),
        )
        if not pago:
            raise api_error(404, "PAGO_NO_ENCONTRADO", "Pago no encontrado")

        if pago["estado"] != "completado":
            raise api_error(
                409,
                "ESTADO_INVALIDO",
                f"Solo se pueden reembolsar pagos completados (estado: {pago['estado']})",
            )

        monto_original = Decimal(str(pago["monto"]))
        if monto is not None:
            monto_reembolso = Decimal(str(monto))
            if monto_reembolso <= 0 or monto_reembolso > monto_original:
                raise api_error(
                    400,
                    "MONTO_INVALIDO",
                    f"El monto de reembolso debe ser > 0 y <= monto original ({monto_original})",
                )
        else:
            monto_reembolso = monto_original

        refund_id = None
        pasarela_id = pago["pasarela_id"]
        if pasarela_id:
            gateway = get_gateway()
            monto_centavos = int((monto_reembolso * 100).quantize(Decimal("1")))
            try:
                refund_res = await gateway.reembolsar(pasarela_id, monto_centavos)
                refund_id = refund_res.get("id")
            except Exception as exc:
                logger.error("Error al emitir reembolso en pasarela: %s", str(exc))
                raise api_error(
                    502,
                    "ERROR_PASARELA",
                    f"Error al procesar reembolso en Stripe: {str(exc)}",
                )

        ref_nota = f" [Reemb {monto_reembolso}: {motivo_final}]"
        nueva_referencia = f"{pago['referencia'] or ''}{ref_nota}"[:100]

        await conn.execute(
            """
            UPDATE pago
               SET estado = 'reembolsado',
                   referencia = $1
             WHERE id = $2 AND empresa_id = $3
            """,
            nueva_referencia,
            UUID(pago_id),
            UUID(empresa_id),
        )

        venta_estado_anterior = pago["venta_estado"]
        venta_estado_nuevo = "devuelta" if venta_estado_anterior not in ("anulada", "devuelta") else venta_estado_anterior
        if venta_estado_nuevo != venta_estado_anterior:
            await conn.execute(
                """
                UPDATE venta
                   SET estado = $1,
                       updated_at = now()
                 WHERE id = $2 AND empresa_id = $3
                """,
                venta_estado_nuevo,
                pago["venta_id"],
                UUID(empresa_id),
            )
            await conn.execute(
                """
                INSERT INTO venta_estado_historial (
                    empresa_id, venta_id, estado_anterior, estado_nuevo, motivo, usuario_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                UUID(empresa_id),
                pago["venta_id"],
                venta_estado_anterior,
                venta_estado_nuevo,
                f"Reembolso de pago ({monto_reembolso}): {motivo_final}"[:200],
                UUID(user_id) if user_id else None,
            )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="superadmin" if rol == "superadmin" else "usuario",
        accion="update",
        entidad="pago",
        entidad_id=pago_id,
        datos_antes={"estado": "completado", "venta_estado": venta_estado_anterior},
        datos_despues={
            "estado": "reembolsado",
            "venta_estado": venta_estado_nuevo,
            "monto_reembolsado": float(monto_reembolso),
            "refund_id": refund_id,
            "motivo": motivo_final,
        },
        ip=ip,
        es_accion_superadmin=(rol == "superadmin"),
        metodo="POST",
        endpoint=f"/api/v1/pagos/{pago_id}/reembolsar",
    )

    return {
        "ok": True,
        "pago_id": str(pago_id),
        "venta_id": str(pago["venta_id"]),
        "estado": "reembolsado",
        "venta_estado": venta_estado_nuevo,
        "monto_reembolsado": float(monto_reembolso),
        "refund_id": refund_id,
        "motivo": motivo_final,
    }


class PagoService:
    def __init__(self, pool=None):
        self.pool = pool

    async def crear_intencion_pago(
        self,
        empresa_id: str,
        datos=None,
        user_id: Optional[str] = None,
        rol: str = "cliente",
        idempotency_key: str = "service-call",
    ):
        venta_id = str(getattr(datos, "venta_id", "") or (datos.get("venta_id") if isinstance(datos, dict) else ""))
        return await crear_intencion_pago(
            empresa_id=empresa_id,
            user_id=user_id or empresa_id,
            rol=rol,
            venta_id=venta_id,
            idempotency_key=idempotency_key,
        )

    async def consultar_pago(self, empresa_id: str, pago_id: str, user_id: Optional[str] = None, rol: str = "administrador"):
        return await get_pago(
            empresa_id=empresa_id,
            user_id=user_id or empresa_id,
            rol=rol,
            pago_id=pago_id,
        )

    async def solicitar_reembolso(
        self,
        empresa_id: str,
        pago_id: str,
        datos=None,
        user_id: Optional[str] = None,
        rol: str = "administrador",
    ):
        monto = getattr(datos, "monto", None) if datos is not None else None
        motivo = getattr(datos, "motivo", None) if datos is not None else None
        return await reembolsar_pago(
            empresa_id=empresa_id,
            pago_id=pago_id,
            user_id=user_id,
            rol=rol,
            monto=monto,
            motivo=motivo,
        )
