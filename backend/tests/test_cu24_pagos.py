from types import SimpleNamespace
import uuid
import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from app.services import pago_service
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_crear_intencion_pago_con_orden(client: AsyncClient):
    """CU-24: Genera PaymentIntent en Stripe sandbox para una orden existente."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())}

    # Asegurar ítem en carrito y crear orden
    await client.post(
        f"{BASE}/carrito/items",
        headers=headers,
        json={"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1},
    )

    orden_res = await client.post(
        f"{BASE}/checkout/ordenes",
        headers=headers,
        json={"tipo_entrega": "recojo", "sucursal_id": "11111111-1111-1111-1111-111111111101"},
    )
    assert orden_res.status_code == 201
    venta_id = orden_res.json()["venta_id"]

    # Crear intención de pago
    resp = await client.post(
        f"{BASE}/pagos/intencion",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
        json={"venta_id": venta_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "client_secret" in data
    assert "publishable_key" in data
    assert data["monto"] > 0
    assert "pago_id" in data


@pytest.mark.asyncio
async def test_webhook_stripe_procesamiento(client: AsyncClient):
    """CU-24: Webhook procesa evento de pasarela e idempotencia."""
    event_id = f"evt_test_{uuid.uuid4().hex[:12]}"
    payload = {
        "id": event_id,
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_sample_123",
                "metadata": {
                    "empresa_id": "11111111-1111-1111-1111-111111111111",
                    "venta_id": "11111111-1111-1111-1111-111111111b01",
                },
            }
        },
    }

    resp1 = await client.post(f"{BASE}/pagos/webhook/stripe", json=payload)
    assert resp1.status_code == 200

    # Segundo envío del mismo evento: idempotente sin error
    resp2 = await client.post(f"{BASE}/pagos/webhook/stripe", json=payload)
    assert resp2.status_code == 200
    assert resp2.json().get("status") == "already_processed"


@pytest.mark.asyncio
async def test_polling_estado_pago(client: AsyncClient):
    """CU-24: Consulta de estado de pago para polling del frontend."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]

    venta_id = "11111111-1111-1111-1111-111111111b01"
    resp = await client.get(
        f"{BASE}/pagos/ventas/{venta_id}/estado-pago",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "venta_estado" in data


@pytest.mark.asyncio
async def test_listar_pagos_y_detalle(client: AsyncClient):
    """CU-24: Listado real GET /api/v1/pagos con paginación y control por rol."""
    r_adm = await login(client, "admin@demo.test", "Admin123!")
    assert r_adm.status_code == 200
    adm_headers = {"Authorization": f"Bearer {r_adm.json()['access_token']}"}

    listed = await client.get(f"{BASE}/pagos", params={"page": 1, "page_size": 10}, headers=adm_headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    pago_id = body["items"][0]["id"]

    det = await client.get(f"{BASE}/pagos/{pago_id}", headers=adm_headers)
    assert det.status_code == 200, det.text
    assert det.json()["id"] == pago_id


@pytest.mark.asyncio
async def test_reembolso_pago_y_validaciones(client: AsyncClient):
    """CU-24: POST /api/v1/pagos/{id}/reembolsar reembolsa pago completado y valida rol/monto."""
    r_cli = await login(client, "cliente@demo.test", "Cliente123!")
    cli_token = r_cli.json()["access_token"]
    cli_headers = {"Authorization": f"Bearer {cli_token}", "Idempotency-Key": str(uuid.uuid4())}

    await client.post(
        f"{BASE}/carrito/items",
        headers=cli_headers,
        json={"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1},
    )
    orden = await client.post(
        f"{BASE}/checkout/ordenes",
        headers=cli_headers,
        json={"tipo_entrega": "recojo", "sucursal_id": "11111111-1111-1111-1111-111111111101"},
    )
    assert orden.status_code == 201, orden.text
    venta_id = orden.json()["venta_id"]

    intencion = await client.post(
        f"{BASE}/pagos/intencion",
        headers={"Authorization": f"Bearer {cli_token}", "Idempotency-Key": str(uuid.uuid4())},
        json={"venta_id": venta_id},
    )
    assert intencion.status_code == 200, intencion.text
    pago_id = intencion.json()["pago_id"]

    wh = await client.post(
        f"{BASE}/pagos/webhook/stripe",
        json={
            "id": f"evt_ref_{uuid.uuid4().hex[:10]}",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_mock_ref",
                    "latest_charge": "ch_mock_ref",
                    "metadata": {
                        "empresa_id": "11111111-1111-1111-1111-111111111111",
                        "venta_id": venta_id,
                        "pago_id": pago_id,
                    },
                }
            },
        },
    )
    assert wh.status_code == 200, wh.text

    # Cliente no puede reembolsar
    forb = await client.post(
        f"{BASE}/pagos/{pago_id}/reembolsar",
        headers={"Authorization": f"Bearer {cli_token}"},
        json={"motivo": "Intento cliente"},
    )
    assert forb.status_code == 403

    r_adm = await login(client, "admin@demo.test", "Admin123!")
    adm_headers = {"Authorization": f"Bearer {r_adm.json()['access_token']}"}

    excess = await client.post(
        f"{BASE}/pagos/{pago_id}/reembolsar",
        headers=adm_headers,
        json={"monto": 999999.0, "motivo": "Exceso"},
    )
    assert excess.status_code == 400

    ok_ref = await client.post(
        f"{BASE}/pagos/{pago_id}/reembolsar",
        headers=adm_headers,
        json={"motivo": "Devolución aprobada"},
    )
    assert ok_ref.status_code == 200, ok_ref.text
    ref_body = ok_ref.json()
    assert ref_body["estado"] == "reembolsado"
    assert ref_body["venta_estado"] == "devuelta"


# ---------------------------------------------------------------------------
# Tests unitarios offline con mocks de Stripe SDK (sin requerir PostgreSQL)
# ---------------------------------------------------------------------------

def test_cu24_offline_gateway_selection(monkeypatch):
    """CU-24 (offline): get_gateway exige STRIPE_SECRET_KEY en runtime y usa StripeGateway si existe."""
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_ALLOW_MOCK", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(pago_service, "STRIPE_SECRET_KEY", "")
    monkeypatch.setattr(
        pago_service,
        "get_settings",
        lambda: SimpleNamespace(
            stripe_secret_key="",
            stripe_publishable_key="pk_test_demo",
            stripe_webhook_secret="",
            payment_currency="usd",
        ),
    )

    with pytest.raises(HTTPException) as exc:
        pago_service.get_gateway()
    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "PASARELA_NO_CONFIGURADA"

    monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_cu24_offline_gateway_selection")
    assert isinstance(pago_service.get_gateway(), pago_service.MockGateway)

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("STRIPE_ALLOW_MOCK", "true")
    assert isinstance(pago_service.get_gateway(), pago_service.MockGateway)
    monkeypatch.delenv("STRIPE_ALLOW_MOCK", raising=False)

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_sandbox_fake_key")
    gw = pago_service.get_gateway()
    assert isinstance(gw, pago_service.StripeGateway)


@pytest.mark.asyncio
async def test_cu24_offline_stripe_gateway_operations(monkeypatch):
    """CU-24 (offline): StripeGateway crea, consulta, confirma PaymentIntents y emite Refund via SDK."""
    import stripe

    calls = {}

    def fake_create(**kwargs):
        calls["create"] = kwargs
        return SimpleNamespace(id="pi_test_123", client_secret="pi_test_123_secret_abc", status="requires_payment_method")

    def fake_retrieve(pi_id):
        calls["retrieve"] = pi_id
        return SimpleNamespace(id=pi_id, status="succeeded", latest_charge="ch_test_1", metadata={"venta_id": "v1"})

    def fake_confirm(pi_id, **kwargs):
        calls["confirm"] = (pi_id, kwargs)
        return SimpleNamespace(id=pi_id, status="succeeded", latest_charge="ch_test_2")

    def fake_refund(**kwargs):
        calls["refund"] = kwargs
        return SimpleNamespace(id="re_test_999", status="succeeded")

    monkeypatch.setattr(stripe.PaymentIntent, "create", fake_create)
    monkeypatch.setattr(stripe.PaymentIntent, "retrieve", fake_retrieve)
    monkeypatch.setattr(stripe.PaymentIntent, "confirm", fake_confirm)
    monkeypatch.setattr(stripe.Refund, "create", fake_refund)

    gw = pago_service.StripeGateway(api_key="sk_test_mock_key")
    intent = await gw.crear_intencion(2500, "usd", {"venta_id": "v1"}, "idem-1")
    assert intent["id"] == "pi_test_123"
    assert intent["client_secret"] == "pi_test_123_secret_abc"
    assert calls["create"]["amount"] == 2500
    assert calls["create"]["automatic_payment_methods"] == {"enabled": True, "allow_redirects": "never"}

    consulted = await gw.consultar_intencion("pi_test_123")
    assert consulted["status"] == "succeeded"

    confirmed = await gw.confirmar_intencion("pi_test_123", "pm_card_visa")
    assert confirmed["latest_charge"] == "ch_test_2"

    refund = await gw.reembolsar("pi_test_123", 1500)
    assert refund["id"] == "re_test_999"
    assert calls["refund"]["amount"] == 1500


@pytest.mark.asyncio
async def test_cu24_offline_webhook_firma_y_conciliacion(monkeypatch):
    """CU-24 (offline): Valida Stripe-Signature HMAC, idempotencia de evento y conciliación de venta."""
    import stripe
    from app.services import checkout_service

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")

    # 1. Sin cabecera Stripe-Signature -> 400 FIRMA_REQUERIDA
    with pytest.raises(HTTPException) as exc_missing:
        await pago_service.procesar_webhook_stripe(b"{}", signature=None)
    assert exc_missing.value.status_code == 400
    assert exc_missing.value.detail["code"] == "FIRMA_REQUERIDA"

    # 2. Firma inválida -> 400 FIRMA_INVALIDA
    def bad_construct_event(payload, sig_header, secret):
        raise ValueError("Invalid signature")

    monkeypatch.setattr(stripe.Webhook, "construct_event", bad_construct_event)
    with pytest.raises(HTTPException) as exc_bad:
        await pago_service.procesar_webhook_stripe(b"{}", signature="t=1,v1=bad")
    assert exc_bad.value.status_code == 400
    assert exc_bad.value.detail["code"] == "FIRMA_INVALIDA"

    # 3. Firma válida + evento payment_intent.succeeded + idempotencia en memoria
    processed_events = set()
    finalized_calls = []

    class FakeWhConn:
        async def fetchval(self, sql, *args):
            if "stripe_evento" in sql:
                return args[0] if args[0] in processed_events else None
            return None

        async def execute(self, sql, *args):
            if "INSERT INTO stripe_evento" in sql:
                processed_events.add(args[0])
            return "UPDATE 1"

        def transaction(self):
            class _Tx:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc, tb):
                    pass

            return _Tx()

    class FakeWhPool:
        def acquire(self):
            class _Ctx:
                async def __aenter__(self):
                    return FakeWhConn()

                async def __aexit__(self, exc_type, exc, tb):
                    pass

            return _Ctx()

    emp_id = str(uuid.uuid4())
    venta_id = str(uuid.uuid4())
    pago_id = str(uuid.uuid4())
    fake_event = {
        "id": "evt_signed_001",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_signed_001",
                "latest_charge": "ch_signed_001",
                "metadata": {"empresa_id": emp_id, "venta_id": venta_id, "pago_id": pago_id},
            }
        },
    }

    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda payload, sig_header, secret: fake_event)
    monkeypatch.setattr(pago_service, "get_pool", lambda: FakeWhPool())

    async def fake_finalizar(**kwargs):
        finalized_calls.append(kwargs)

    async def fake_audit(**kwargs):
        return None

    monkeypatch.setattr(checkout_service, "finalizar_venta_pagada", fake_finalizar)
    monkeypatch.setattr(pago_service, "audit_event", fake_audit)

    first = await pago_service.procesar_webhook_stripe(b"{}", signature="t=1,v1=valid")
    assert first["status"] == "success"
    assert len(finalized_calls) == 1
    assert finalized_calls[0]["venta_id"] == venta_id

    second = await pago_service.procesar_webhook_stripe(b"{}", signature="t=1,v1=valid")
    assert second["status"] == "already_processed"
    assert len(finalized_calls) == 1


@pytest.mark.asyncio
async def test_cu24_offline_pos_out_and_finalizar_pos_sin_usuario(monkeypatch):
    """CU-23/24 (offline): PosVentaOut conserva intencion_pago y finalizar_venta_pagada soporta POS y pago_fallido."""
    from contextlib import asynccontextmanager
    from app.schemas.venta import PosVentaOut
    from app.services import checkout_service

    emp_id = uuid.uuid4()
    venta_id = uuid.uuid4()
    suc_id = uuid.uuid4()
    cajero_id = uuid.uuid4()
    var_id = uuid.uuid4()

    out = PosVentaOut(
        venta_id=venta_id,
        numero="POS-1111-00001",
        total=113.0,
        cambio=0.0,
        metodo_pago="tarjeta",
        estado="pendiente_pago",
        comprobante_url=f"/api/v1/ventas/{venta_id}/ticket",
        intencion_pago={
            "pago_id": str(uuid.uuid4()),
            "client_secret": "pi_mock_1_secret_mock",
            "publishable_key": "pk_test_demo",
            "monto": 11300,
            "moneda": "usd",
        },
    )
    assert out.intencion_pago is not None
    assert out.intencion_pago["monto"] == 11300

    executed = []

    class FakeConn:
        async def fetchrow(self, sql, *args):
            if "FROM venta" in sql:
                return {
                    "id": venta_id,
                    "numero": "POS-1111-00001",
                    "estado": "pago_fallido",
                    "sucursal_id": suc_id,
                    "usuario_id": None,
                    "cajero_id": cajero_id,
                    "cupon_id": None,
                    "total": 113.0,
                }
            return None

        async def fetch(self, sql, *args):
            if "FROM venta_detalle" in sql:
                return [{"id": uuid.uuid4(), "variante_id": var_id, "cantidad": 2}]
            if "FROM inventario" in sql:
                return [{"variante_id": var_id, "stock_fisico": 5}]
            return []

        async def execute(self, sql, *args):
            executed.append((sql.strip(), args))
            return "UPDATE 1"

    @asynccontextmanager
    async def fake_tenant_conn(*args, **kwargs):
        yield FakeConn()

    async def fake_audit(**kwargs):
        return None

    monkeypatch.setattr(checkout_service, "tenant_connection", fake_tenant_conn)
    monkeypatch.setattr(checkout_service, "audit_event", fake_audit)

    await checkout_service.finalizar_venta_pagada(
        empresa_id=str(emp_id),
        venta_id=str(venta_id),
        pago_id=str(uuid.uuid4()),
    )

    mov_calls = [args for sql, args in executed if "INSERT INTO movimiento_inventario" in sql]
    assert len(mov_calls) == 1
    assert mov_calls[0][-1] == cajero_id
    assert not any("UPDATE carrito" in sql for sql, _ in executed)


@pytest.mark.asyncio
async def test_cu24_offline_pos_tarjeta_commits_before_intencion(monkeypatch):
    """CU-23/24 (offline): crear_venta_pos con tarjeta confirma la transacción antes de crear la intención Stripe."""
    from contextlib import asynccontextmanager
    from app.services import pos_service

    emp_id = uuid.uuid4()
    cajero_id = uuid.uuid4()
    suc_id = uuid.uuid4()
    var_id = uuid.uuid4()
    venta_id = uuid.uuid4()

    tx_state = {"in_tx": False, "committed": False, "seen_committed_in_intencion": False}

    class FakePosConn:
        async def fetchrow(self, sql, *args):
            if "idempotency_key" in sql and "FROM venta" in sql:
                return None
            if "FROM usuario" in sql:
                return {"sucursal_id": suc_id}
            if "INSERT INTO venta" in sql:
                return {"id": venta_id}
            return None

        async def fetchval(self, sql, *args):
            if "FROM sucursal" in sql:
                return suc_id
            if "COUNT(*) + 1 FROM venta" in sql:
                return 7
            if "SELECT now()" in sql:
                return "2026-11-11 22:00:00+00"
            return None

        async def fetch(self, sql, *args):
            if "FROM variante" in sql:
                return [{"id": var_id, "precio_venta": 100.0, "sku": "SKU-1"}]
            if "FROM inventario" in sql:
                return [{"variante_id": var_id, "stock_fisico": 4, "stock_reservado": 0, "stock_disponible": 4}]
            return []

        async def execute(self, sql, *args):
            return "INSERT 0 1"

    @asynccontextmanager
    async def fake_tenant_conn(*args, **kwargs):
        tx_state["in_tx"] = True
        try:
            yield FakePosConn()
        finally:
            tx_state["in_tx"] = False
            tx_state["committed"] = True

    async def fake_crear_intencion_pago(**kwargs):
        tx_state["seen_committed_in_intencion"] = tx_state["committed"] and not tx_state["in_tx"]
        assert tx_state["seen_committed_in_intencion"] is True
        return {
            "pago_id": str(uuid.uuid4()),
            "client_secret": "pi_mock_secret",
            "publishable_key": "pk_test_demo",
            "monto": 11300,
            "moneda": "usd",
        }

    async def fake_audit(**kwargs):
        return None

    monkeypatch.setattr(pos_service, "tenant_connection", fake_tenant_conn)
    monkeypatch.setattr(pos_service, "audit_event", fake_audit)
    monkeypatch.setattr(pago_service, "crear_intencion_pago", fake_crear_intencion_pago)

    res = await pos_service.crear_venta_pos(
        empresa_id=str(emp_id),
        user_id=str(cajero_id),
        rol="cajero",
        idempotency_key="pos-card-idem-1",
        items=[{"variante_id": str(var_id), "cantidad": 1}],
        cliente={"tipo": "consumidor_final"},
        pago={"metodo": "tarjeta"},
    )

    assert tx_state["seen_committed_in_intencion"] is True
    assert res["estado"] == "pendiente_pago"
    assert res["metodo_pago"] == "tarjeta"
    assert res["intencion_pago"]["monto"] == 11300


