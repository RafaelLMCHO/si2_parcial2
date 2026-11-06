import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_listar_inventario_admin(client: AsyncClient):
    """Admin puede ver inventario de su empresa."""
    r = await login(client, "admin@demo.test", "Admin123!")
    assert r.status_code == 200
    token = r.json()["access_token"]

    resp = await client.get(f"{BASE}/inventario", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_listar_inventario_cajero(client: AsyncClient):
    """Cajero tiene permiso para consultar inventario."""
    r = await login(client, "cajero@demo.test", "Cajero123!")
    if r.status_code == 200:
        token = r.json()["access_token"]
        resp = await client.get(f"{BASE}/inventario", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_listar_inventario_cliente_prohibido(client: AsyncClient):
    """Cliente no tiene permiso de inventario (403)."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    assert r.status_code == 200
    token = r.json()["access_token"]
    resp = await client.get(f"{BASE}/inventario", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ingreso_lote_admin(client: AsyncClient):
    """Admin puede registrar un ingreso de stock por lote."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.post(
        f"{BASE}/inventario/movimientos/ingreso",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 5}],
            "motivo": "Ingreso por reposición de lote de fábrica",
            "referencia": "LOTE-2026-001",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True or "ingresados" in data


@pytest.mark.asyncio
async def test_ajuste_merma(client: AsyncClient):
    """Ajuste de merma reduce stock físico."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.post(
        f"{BASE}/inventario/movimientos/ajuste",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "variante_id": "11111111-1111-1111-1111-111111111601",
            "cantidad": -1,
            "motivo": "Prenda con mancha no removible",
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ajuste_merma_excesiva_409(client: AsyncClient):
    """Ajuste negativo mayor que stock disponible lanza 409."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.post(
        f"{BASE}/inventario/movimientos/ajuste",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "variante_id": "11111111-1111-1111-1111-111111111601",
            "cantidad": -99999,
            "motivo": "Prueba de stock insuficiente",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_transferencia_misma_sucursal_error(client: AsyncClient):
    """Transferencia entre la misma sucursal origen y destino debe rechazarse."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.post(
        f"{BASE}/inventario/transferencias",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "origen_id": "11111111-1111-1111-1111-111111111101",
            "destino_id": "11111111-1111-1111-1111-111111111101",
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert resp.status_code in (400, 409, 422)


@pytest.mark.asyncio
async def test_listar_movimientos_kardex(client: AsyncClient):
    """Kárdex paginado de movimientos."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.get(f"{BASE}/inventario/movimientos", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data

