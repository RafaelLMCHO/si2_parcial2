import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_disponibilidad_prenda_online(client: AsyncClient):
    """CU-18: Cliente consulta existencias en tiempo real de una prenda por sucursales."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    assert r.status_code == 200
    token = r.json()["access_token"]

    prenda_id = "11111111-1111-1111-1111-111111111501"
    resp = await client.get(
        f"{BASE}/prendas/{prenda_id}/disponibilidad",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert str(data["prenda_id"]) == prenda_id
    assert "agotado_en_todas" in data
    assert "sucursales" in data
    assert len(data["sucursales"]) >= 1

    sucursal = data["sucursales"][0]
    assert "nombre" in sucursal
    assert "direccion" in sucursal
    assert "variantes" in sucursal
    assert len(sucursal["variantes"]) >= 1
    var = sucursal["variantes"][0]
    assert "stock_disponible" in var
    assert "talla" in var
    assert "color" in var


@pytest.mark.asyncio
async def test_disponibilidad_via_inventario_alias(client: AsyncClient):
    """CU-18: Consulta mediante el endpoint anidado en inventario."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    prenda_id = "11111111-1111-1111-1111-111111111501"
    resp = await client.get(
        f"{BASE}/inventario/prendas/{prenda_id}/disponibilidad",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "sucursales" in data

