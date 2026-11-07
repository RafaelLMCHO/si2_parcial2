import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_validar_reserva_ok(client: AsyncClient):
    """CU-19: Validación sin efectos secundarios de disponibilidad para reserva."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]

    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    resp = await client.post(
        f"{BASE}/reservas/validar",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": fecha_futura,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


@pytest.mark.asyncio
async def test_crear_reserva_correcta(client: AsyncClient):
    """CU-19: Cliente realiza reserva de prendas generando código digital."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]
    idempotency_key = str(uuid.uuid4())

    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    resp = await client.post(
        f"{BASE}/reservas",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": fecha_futura,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "codigo" in data
    assert data["codigo"].startswith("RSV-")
    assert data["estado"] == "pendiente_preparacion"
    assert "items" in data
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_crear_reserva_idempotencia(client: AsyncClient):
    """CU-19: Reenvío con el mismo Idempotency-Key devuelve la misma reserva."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]
    idempotency_key = str(uuid.uuid4())
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": idempotency_key}
    body = {
        "sucursal_id": "11111111-1111-1111-1111-111111111101",
        "fecha_visita": fecha_futura,
        "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
    }

    resp1 = await client.post(f"{BASE}/reservas", headers=headers, json=body)
    resp2 = await client.post(f"{BASE}/reservas", headers=headers, json=body)

    assert resp1.status_code == 201
    assert resp2.status_code in (200, 201)
    assert resp1.json()["id"] == resp2.json()["id"]
    assert resp1.json()["codigo"] == resp2.json()["codigo"]


@pytest.mark.asyncio
async def test_crear_reserva_fecha_pasada_422(client: AsyncClient):
    """CU-19: Fecha tentativa en el pasado se rechaza con 422."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]

    resp = await client.post(
        f"{BASE}/reservas",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": "2020-01-01T10:00:00Z",
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert resp.status_code == 422

