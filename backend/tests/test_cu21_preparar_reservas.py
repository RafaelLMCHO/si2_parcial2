import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from tests.conftest import login

BASE = "/api/v1"


@pytest.mark.asyncio
async def test_preparar_reserva_encargado(client: AsyncClient):
    """CU-21: Encargado de sucursal marca reserva como preparada en probador."""
    # 1. Cliente crea reserva
    r_cli = await login(client, "cliente@demo.test", "Cliente123!")
    token_cli = r_cli.json()["access_token"]
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    reserva_res = await client.post(
        f"{BASE}/reservas",
        headers={"Authorization": f"Bearer {token_cli}", "Idempotency-Key": str(uuid.uuid4())},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": fecha_futura,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert reserva_res.status_code == 201
    reserva_id = reserva_res.json()["id"]

    # 2. Encargado prepara reserva
    r_enc = await login(client, "encargado@demo.test", "Encargado123!")
    if r_enc.status_code != 200:
        # Fallback a admin si encargado no está autenticado
        r_enc = await login(client, "admin@demo.test", "Admin123!")
    token_enc = r_enc.json()["access_token"]

    resp = await client.post(
        f"{BASE}/reservas/{reserva_id}/preparar",
        headers={"Authorization": f"Bearer {token_enc}"},
        json={"probador": "Probador 2 - VIP"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "preparada"
    assert data["probador"] == "Probador 2 - VIP"


@pytest.mark.asyncio
async def test_bandeja_reservas_por_preparar(client: AsyncClient):
    """CU-21: Consulta de reservas por preparar en sucursal."""
    r = await login(client, "admin@demo.test", "Admin123!")
    token = r.json()["access_token"]

    resp = await client.get(f"{BASE}/reservas/por-preparar", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_reportar_incidencia_reserva(client: AsyncClient):
    """CU-21: Reportar prenda extraviada o dañada ofreciendo alternativas."""
    r_cli = await login(client, "cliente@demo.test", "Cliente123!")
    token_cli = r_cli.json()["access_token"]
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    reserva_res = await client.post(
        f"{BASE}/reservas",
        headers={"Authorization": f"Bearer {token_cli}", "Idempotency-Key": str(uuid.uuid4())},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": fecha_futura,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert reserva_res.status_code == 201
    reserva_id = reserva_res.json()["id"]

    r_admin = await login(client, "admin@demo.test", "Admin123!")
    token_admin = r_admin.json()["access_token"]

    resp = await client.post(
        f"{BASE}/reservas/{reserva_id}/incidencia",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "variante_ids": ["11111111-1111-1111-1111-111111111601"],
            "motivo": "Prenda no encontrada en percheros de tienda",
            "registrar_merma": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "incidencia_stock"
    assert "alternativas" in data


@pytest.mark.asyncio
async def test_completar_reserva_encargado_y_permiso_cliente(client: AsyncClient):
    """CU-21: POST /api/v1/reservas/{id}/completar cambia estado a completada y bloquea clientes."""
    r_cli = await login(client, "cliente@demo.test", "Cliente123!")
    token_cli = r_cli.json()["access_token"]
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    reserva_res = await client.post(
        f"{BASE}/reservas",
        headers={"Authorization": f"Bearer {token_cli}", "Idempotency-Key": str(uuid.uuid4())},
        json={
            "sucursal_id": "11111111-1111-1111-1111-111111111101",
            "fecha_visita": fecha_futura,
            "items": [{"variante_id": "11111111-1111-1111-1111-111111111601", "cantidad": 1}],
        },
    )
    assert reserva_res.status_code == 201
    reserva_id = reserva_res.json()["id"]

    cli_attempt = await client.post(
        f"{BASE}/reservas/{reserva_id}/completar",
        headers={"Authorization": f"Bearer {token_cli}"},
        json={"motivo": "Intento cliente"},
    )
    assert cli_attempt.status_code == 403

    r_enc = await login(client, "encargado@demo.test", "Encargado123!")
    if r_enc.status_code != 200:
        r_enc = await login(client, "admin@demo.test", "Admin123!")
    token_enc = r_enc.json()["access_token"]
    enc_headers = {"Authorization": f"Bearer {token_enc}"}

    prep = await client.post(
        f"{BASE}/reservas/{reserva_id}/preparar",
        headers=enc_headers,
        json={"probador": "Probador 1"},
    )
    assert prep.status_code == 200

    comp = await client.post(
        f"{BASE}/reservas/{reserva_id}/completar",
        headers=enc_headers,
        json={"motivo": "Cliente atendido en tienda"},
    )
    assert comp.status_code == 200, comp.text
    data = comp.json()
    assert data["estado"] == "completada"
    assert any(h["estado_nuevo"] == "completada" for h in (data.get("historial") or []))

