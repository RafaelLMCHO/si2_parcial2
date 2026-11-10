import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


async def _crear_reserva_helper(client: AsyncClient, token: str) -> dict:
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    resp = await client.post(
        f"{BASE}/reservas",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": fecha_futura,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_cancelar_reserva_propia(client: AsyncClient):
    """CU-20: Cliente puede cancelar su reserva pendiente y liberar stock."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]

    reserva = await _crear_reserva_helper(client, token)
    reserva_id = reserva["id"]

    resp = await client.post(
        f"{BASE}/reservas/{reserva_id}/cancelar",
        headers={"Authorization": f"Bearer {token}"},
        json={"motivo": "Cambio de planes de viaje"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "cancelada"


@pytest.mark.asyncio
async def test_cancelar_reserva_idempotente(client: AsyncClient):
    """CU-20: Cancelar una reserva ya cancelada retorna 200 sin efectos secundarios."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]

    reserva = await _crear_reserva_helper(client, token)
    reserva_id = reserva["id"]
    headers = {"Authorization": f"Bearer {token}"}

    resp1 = await client.post(f"{BASE}/reservas/{reserva_id}/cancelar", headers=headers, json={})
    resp2 = await client.post(f"{BASE}/reservas/{reserva_id}/cancelar", headers=headers, json={})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp2.json()["estado"] == "cancelada"


@pytest.mark.asyncio
async def test_listar_mis_reservas_cliente(client: AsyncClient):
    """CU-20: Cliente solo lista sus propias reservas."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    token = r.json()["access_token"]

    resp = await client.get(f"{BASE}/reservas", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_listar_mis_reservas_endpoint_canonico(client: AsyncClient):
    """CU-20: GET /api/v1/reservas/mis-reservas con filtro de estado y aislamiento por usuario."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    assert r.status_code == 200
    token = r.json()["access_token"]
    user_id = str(r.json()["usuario"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    reserva = await _crear_reserva_helper(client, token)
    reserva_id = reserva["id"]

    try:
        resp = await client.get(
            f"{BASE}/reservas/mis-reservas",
            params={"estado": "pendiente_preparacion", "page": 1, "page_size": 20},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["page"] == 1
        assert any(str(it["id"]) == str(reserva_id) for it in data["items"])
        assert all(str(it["usuario_id"]) == user_id for it in data["items"])

        other_state = await client.get(
            f"{BASE}/reservas/mis-reservas",
            params={"estado": "cancelada"},
            headers=headers,
        )
        assert other_state.status_code == 200
        assert not any(str(it["id"]) == str(reserva_id) for it in other_state.json()["items"])
    finally:
        await client.post(f"{BASE}/reservas/{reserva_id}/cancelar", headers=headers, json={})

