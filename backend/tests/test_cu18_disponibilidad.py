import pytest
from httpx import AsyncClient
from app.main import app
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_disponibilidad_prenda_canonica(client: AsyncClient):
    """CU-18 (canónico): GET /api/v1/inventario/prendas/{prenda_id}/disponibilidad."""
    r = await login(client, "cliente@demo.test", "Cliente123!")
    assert r.status_code == 200
    token = r.json()["access_token"]

    prenda_id = "11111111-1111-1111-1111-111111111501"
    resp = await client.get(
        f"{BASE}/inventario/prendas/{prenda_id}/disponibilidad",
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
async def test_disponibilidad_ruta_deprecada_compatible(client: AsyncClient):
    """CU-18: Ruta legacy /api/v1/prendas/{id}/disponibilidad se mantiene compatible pero deprecada."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    prenda_id = "11111111-1111-1111-1111-111111111501"
    resp = await client.get(
        f"{BASE}/prendas/{prenda_id}/disponibilidad",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "sucursales" in resp.json()


def test_cu18_offline_contrato_canonico_y_deprecado_openapi():
    """CU-18 (offline): Verifica ruta canónica activa y legacy marcada deprecated=True en OpenAPI."""
    schema = app.openapi()
    paths = schema["paths"]
    canonical = "/api/v1/inventario/prendas/{prenda_id}/disponibilidad"
    legacy = "/api/v1/prendas/{prenda_id}/disponibilidad"
    assert canonical in paths
    assert "get" in paths[canonical]
    assert paths[canonical]["get"].get("deprecated") is not True
    assert legacy in paths
    assert paths[legacy]["get"].get("deprecated") is True

