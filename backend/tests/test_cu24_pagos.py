import uuid
import pytest
from httpx import AsyncClient
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

