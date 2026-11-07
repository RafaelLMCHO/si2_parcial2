import uuid
import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_carrito_gestion_completa(client: AsyncClient):
    """CU-22: Operaciones CRUD del carrito del cliente."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Agregar ítem
    resp_add = await client.post(
        f"{BASE}/carrito/items",
        headers=headers,
        json={"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 2},
    )
    assert resp_add.status_code == 200
    data = resp_add.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    item_id = data["items"][0]["id"]

    # 2. Modificar cantidad
    resp_mod = await client.patch(
        f"{BASE}/carrito/items/{item_id}",
        headers=headers,
        json={"cantidad": 3},
    )
    assert resp_mod.status_code == 200

    # 3. Consultar carrito
    resp_get = await client.get(f"{BASE}/carrito", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["total"] > 0


@pytest.mark.asyncio
async def test_checkout_validar_recojo(client: AsyncClient):
    """CU-22: Validar checkout con entrega tipo recojo en sucursal."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Asegurar ítem en carrito
    await client.post(
        f"{BASE}/carrito/items",
        headers=headers,
        json={"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1},
    )

    resp = await client.post(
        f"{BASE}/checkout/validar",
        headers=headers,
        json={
            "tipo_entrega": "recojo",
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_a_pagar" in data
    assert "subtotal" in data
    assert "impuesto" in data
    assert data["costo_envio"] == 0


@pytest.mark.asyncio
async def test_crear_orden_compra_idempotencia(client: AsyncClient):
    """CU-22: Creación de orden pendiente de cobro con Idempotency-Key."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]
    idempotency_key = str(uuid.uuid4())

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": idempotency_key}
    body = {
        "tipo_entrega": "recojo",
        "sucursal_id": "11111111-1111-1111-1111-111111111101",
    }

    # Asegurar ítem en carrito
    await client.post(
        f"{BASE}/carrito/items",
        headers=headers,
        json={"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1},
    )

    resp1 = await client.post(f"{BASE}/checkout/ordenes", headers=headers, json=body)
    resp2 = await client.post(f"{BASE}/checkout/ordenes", headers=headers, json=body)

    assert resp1.status_code == 201
    assert resp2.status_code in (200, 201)
    assert resp1.json()["venta_id"] == resp2.json()["venta_id"]
    assert resp1.json()["numero"] == resp2.json()["numero"]

