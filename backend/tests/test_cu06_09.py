from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.db import get_pool
from tests.conftest import login

SUPERADMIN = ("superadmin@fashionstore.test", "Superadmin123!")


async def _superadmin_headers(client: AsyncClient) -> dict[str, str]:
    response = await login(client, SUPERADMIN[0], SUPERADMIN[1], empresa_slug=None)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _company_payload() -> dict:
    suffix = uuid4().hex[:10]
    return {
        "nombre": f"Empresa {suffix}",
        "nit": f"T{suffix}",
        "telefono": "70000001",
        "direccion": "Av. Principal 123",
        "correo_admin": f"admin{suffix}@tenant.test",
        "nombre_admin": "Administrador Tenant",
    }


async def _delete_company(company_id: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL session_replication_role = 'replica'")
            await conn.execute("DELETE FROM empresa WHERE id = $1", UUID(company_id))


@pytest.mark.asyncio
async def test_cu06_crear_empresa_y_duplicados(client: AsyncClient):
    headers = await _superadmin_headers(client)
    payload = _company_payload()

    response = await client.post("/api/v1/saas/empresas", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["estado"] == "pendiente_plan"
    assert created["admin_correo"] == payload["correo_admin"]
    assert created["password_temporal"]

    try:
        duplicate_nit = {**_company_payload(), "nit": payload["nit"]}
        conflict = await client.post(
            "/api/v1/saas/empresas",
            json=duplicate_nit,
            headers=headers,
        )
        assert conflict.status_code == 409, conflict.text
        assert conflict.json()["detail"]["code"] == "NIT_DUPLICADO"

        duplicate_email = {
            **_company_payload(),
            "correo_admin": payload["correo_admin"],
        }
        conflict = await client.post(
            "/api/v1/saas/empresas",
            json=duplicate_email,
            headers=headers,
        )
        assert conflict.status_code == 409, conflict.text
        assert conflict.json()["detail"]["code"] == "CORREO_ADMIN_DUPLICADO"

        pending_login = await login(
            client,
            payload["correo_admin"],
            created["password_temporal"],
            created["slug"],
        )
        assert pending_login.status_code == 403, pending_login.text
        assert pending_login.json()["detail"]["code"] == "EMPRESA_PENDIENTE_PLAN"

        pool = get_pool()
        async with pool.acquire() as conn:
            roles = await conn.fetchval(
                "SELECT count(*) FROM rol WHERE empresa_id = $1",
                created["empresa_id"],
            )
            admin = await conn.fetchrow(
                "SELECT email_verificado FROM usuario WHERE id = $1",
                created["admin_usuario_id"],
            )
        assert roles == 4
        assert admin["email_verificado"] is True
    finally:
        await _delete_company(created["empresa_id"])


@pytest.mark.asyncio
async def test_cu07_cu08_cu09_flujo_saas(client: AsyncClient):
    headers = await _superadmin_headers(client)
    payload = _company_payload()

    response = await client.post("/api/v1/saas/empresas", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    created = response.json()
    company_id = created["empresa_id"]

    try:
        metrics = await client.get("/api/v1/saas/metricas", headers=headers)
        assert metrics.status_code == 200, metrics.text
        assert metrics.json()["total_tenants"] >= 1

        today = date.today()
        assignment = await client.put(
            f"/api/v1/saas/empresas/{company_id}/suscripcion",
            json={
                "plan_codigo": "basico",
                "fecha_inicio": today.isoformat(),
                "fecha_fin": (today + timedelta(days=30)).isoformat(),
                "estado": "activa",
                "renovacion_auto": True,
            },
            headers=headers,
        )
        assert assignment.status_code == 200, assignment.text
        subscription = assignment.json()["suscripcion"]
        assert subscription["plan"]["codigo"] == "basico"
        assert subscription["limites"]["sucursales"] == 2

        admin_login = await login(
            client,
            payload["correo_admin"],
            created["password_temporal"],
            created["slug"],
        )
        assert admin_login.status_code == 200, admin_login.text
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }

        mine = await client.get("/api/v1/mi-suscripcion", headers=admin_headers)
        assert mine.status_code == 200, mine.text
        assert mine.json()["suscripcion"]["plan"]["codigo"] == "basico"

        listed = await client.get(
            "/api/v1/saas/empresas",
            params={"search": created["slug"]},
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["total"] == 1

        detail = await client.get(f"/api/v1/saas/empresas/{company_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        assert detail.json()["estado"] == "activa"

        upgrade = await client.put(
            f"/api/v1/saas/empresas/{company_id}/suscripcion",
            json={
                "plan_codigo": "profesional",
                "fecha_inicio": (today + timedelta(days=1)).isoformat(),
                "fecha_fin": (today + timedelta(days=31)).isoformat(),
                "estado": "activa",
                "renovacion_auto": False,
            },
            headers=headers,
        )
        assert upgrade.status_code == 200, upgrade.text
        assert upgrade.json()["suscripcion"]["plan"]["codigo"] == "profesional"

        pool = get_pool()
        async with pool.acquire() as conn:
            active = await conn.fetchval(
                """
                SELECT count(*)
                  FROM suscripcion
                 WHERE empresa_id = $1
                   AND estado IN ('prueba', 'activa', 'mora')
                """,
                UUID(company_id),
            )
            canceled = await conn.fetchval(
                "SELECT count(*) FROM suscripcion WHERE empresa_id = $1 AND estado = 'cancelada'",
                UUID(company_id),
            )
        assert active == 1
        assert canceled == 1

        suspended = await client.post(
            f"/api/v1/saas/empresas/{company_id}/suspender",
            json={"motivo": "Prueba de suspension"},
            headers=headers,
        )
        assert suspended.status_code == 200, suspended.text
        assert suspended.json()["estado"] == "suspendida"

        revoked = await client.get("/api/v1/users/me", headers=admin_headers)
        assert revoked.status_code == 401, revoked.text
        assert revoked.json()["detail"]["code"] == "SESION_REVOCADA"

        blocked_login = await login(
            client,
            payload["correo_admin"],
            created["password_temporal"],
            created["slug"],
        )
        assert blocked_login.status_code == 403, blocked_login.text
        assert blocked_login.json()["detail"]["code"] == "EMPRESA_NO_ACTIVA"

        reactivated = await client.post(
            f"/api/v1/saas/empresas/{company_id}/reactivar",
            json={"motivo": "Fin de la prueba"},
            headers=headers,
        )
        assert reactivated.status_code == 200, reactivated.text
        assert reactivated.json()["estado"] == "activa"

        restored_login = await login(
            client,
            payload["correo_admin"],
            created["password_temporal"],
            created["slug"],
        )
        assert restored_login.status_code == 200, restored_login.text
    finally:
        await _delete_company(company_id)


@pytest.mark.asyncio
async def test_cu07_downgrade_bloqueado_por_sucursales(client: AsyncClient):
    headers = await _superadmin_headers(client)
    payload = _company_payload()

    response = await client.post("/api/v1/saas/empresas", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    created = response.json()
    company_id = created["empresa_id"]

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            city_id = await conn.fetchval(
                """
                SELECT id FROM ciudad
                 WHERE nombre = 'Santa Cruz de la Sierra'
                   AND departamento = 'Santa Cruz'
                 LIMIT 1
                """
            )
            for index in range(3):
                await conn.execute(
                    """
                    INSERT INTO sucursal (
                        empresa_id, ciudad_id, nombre, direccion, estado
                    )
                    VALUES ($1, $2, $3, $4, 'activa')
                    """,
                    UUID(company_id),
                    city_id,
                    f"Sucursal Downgrade {index}",
                    f"Calle {index}",
                )

        today = date.today()
        downgrade = await client.put(
            f"/api/v1/saas/empresas/{company_id}/suscripcion",
            json={
                "plan_codigo": "basico",
                "fecha_inicio": today.isoformat(),
                "fecha_fin": (today + timedelta(days=30)).isoformat(),
                "estado": "activa",
                "renovacion_auto": False,
            },
            headers=headers,
        )
        assert downgrade.status_code == 409, downgrade.text
        assert downgrade.json()["detail"]["code"] == "LIMITE_SUCURSALES_EXCEDIDO"
    finally:
        await _delete_company(company_id)


@pytest.mark.asyncio
async def test_cu09_requiere_superadmin(client: AsyncClient):
    response = await login(client, "admin@demo.test", "Admin123!")
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    forbidden = await client.get("/api/v1/saas/metricas", headers=headers)
    assert forbidden.status_code == 403, forbidden.text
    assert forbidden.json()["detail"]["code"] == "SUPERADMIN_REQUERIDO"
