import uuid
import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_pos_buscar_por_barcode(client: AsyncClient):
    """CU-23: Cajero escanea código de barras en mostrador."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.get(
        f"{BASE}/pos/variantes/barcode/FS0001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sku"] == "FS-VES-001-NEG-M"
    assert "stock_disponible" in data
    assert "precio_venta" in data


@pytest.mark.asyncio
async def test_pos_venta_efectivo_exitosa(client: AsyncClient):
    """CU-23: Venta en mostrador pagada en efectivo con cambio."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]
    idempotency_key = str(uuid.uuid4())

    resp = await client.post(
        f"{BASE}/pos/ventas",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "idempotency_key": idempotency_key,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
            "cliente": {"tipo": "consumidor_final"},
            "pago": {"metodo": "efectivo", "monto_recibido": 200.0},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "completada"
    assert data["metodo_pago"] == "efectivo"
    assert data["cambio"] > 0
    assert "comprobante_url" in data
    assert data["numero"].startswith("POS-")


@pytest.mark.asyncio
async def test_pos_efectivo_insuficiente_422(client: AsyncClient):
    """CU-23: Flujo 4.a: Efectivo insuficiente lanza 422 con faltante."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.post(
        f"{BASE}/pos/ventas",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "idempotency_key": str(uuid.uuid4()),
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
            "cliente": {"tipo": "consumidor_final"},
            "pago": {"metodo": "efectivo", "monto_recibido": 10.0},
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pos_venta_idempotente(client: AsyncClient):
    """CU-23: Reenvío con mismo Idempotency-Key no duplica venta ni inventario."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]
    idempotency_key = str(uuid.uuid4())

    body = {
        "idempotency_key": idempotency_key,
        "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        "cliente": {"tipo": "consumidor_final"},
        "pago": {"metodo": "efectivo", "monto_recibido": 200.0},
    }

    resp1 = await client.post(f"{BASE}/pos/ventas", headers={"Authorization": f"Bearer {token}"}, json=body)
    resp2 = await client.post(f"{BASE}/pos/ventas", headers={"Authorization": f"Bearer {token}"}, json=body)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["venta_id"] == resp2.json()["venta_id"]
    assert resp1.json()["numero"] == resp2.json()["numero"]


@pytest.mark.asyncio
async def test_pos_ticket_impresion(client: AsyncClient):
    """CU-23: Obtiene datos del ticket térmico."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    # Crear venta primero
    res_venta = await client.post(
        f"{BASE}/pos/ventas",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "idempotency_key": str(uuid.uuid4()),
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
            "cliente": {"tipo": "consumidor_final"},
            "pago": {"metodo": "efectivo", "monto_recibido": 200.0},
        },
    )
    venta_id = res_venta.json()["venta_id"]

    resp = await client.get(f"{BASE}/pos/ventas/{venta_id}/ticket", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "ticket" in data
    assert data["ticket"]["numero"] == res_venta.json()["numero"]

