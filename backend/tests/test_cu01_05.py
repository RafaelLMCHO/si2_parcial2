from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.db import get_pool
from tests.conftest import login

DEMO_EMPRESA = "11111111-1111-1111-1111-111111111111"


def _unique_email() -> str:
    return f"user{uuid4().hex[:10]}@demo.test"


async def _register_and_verify(client: AsyncClient, email: str, password: str = "Clave123!"):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "empresa_slug": "demo",
            "nombre": "Usuario Prueba",
            "correo": email,
            "telefono": "70000001",
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["verification_token"]
    assert token

    verify = await client.post(
        "/api/v1/auth/verify-email",
        json={"empresa_slug": "demo", "token": token},
    )
    assert verify.status_code == 200, verify.text


@pytest.mark.asyncio
async def test_cu01_login_demo_administrador(client: AsyncClient):
    response = await login(client, "admin@demo.test", "Admin123!")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["usuario"]["rol"] == "administrador"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_cu01_login_password_incorrecta(client: AsyncClient):
    response = await login(client, "admin@demo.test", "Incorrecta123!")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "CREDENCIALES_INVALIDAS"


@pytest.mark.asyncio
async def test_cu01_login_tenant_inexistente(client: AsyncClient):
    response = await login(client, "admin@demo.test", "Admin123!", empresa_slug="no-existe")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cu01_login_superadmin_global(client: AsyncClient):
    response = await login(client, "superadmin@fashionstore.test", "Superadmin123!", empresa_slug=None)
    assert response.status_code == 200, response.text
    assert response.json()["usuario"]["empresa_id"] is None
    assert response.json()["usuario"]["rol"] == "superadmin"


@pytest.mark.asyncio
async def test_cu01_suscripcion_suspendida_bloquea_login(client: AsyncClient):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE suscripcion SET estado = 'suspendida' WHERE empresa_id = $1",
            DEMO_EMPRESA,
        )
    try:
        response = await login(client, "admin@demo.test", "Admin123!")
        assert response.status_code == 402
        assert response.json()["detail"]["code"] == "SUSCRIPCION_INACTIVA"
    finally:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE suscripcion SET estado = 'activa' WHERE empresa_id = $1",
                DEMO_EMPRESA,
            )


@pytest.mark.asyncio
async def test_cu02_registro_requiere_verificacion(client: AsyncClient):
    email = _unique_email()
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "empresa_slug": "demo",
            "nombre": "Sin Verificar",
            "correo": email,
            "password": "Clave123!",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["email_verificado"] is False

    before = await login(client, email, "Clave123!")
    assert before.status_code == 403
    assert before.json()["detail"]["code"] == "EMAIL_NO_VERIFICADO"


@pytest.mark.asyncio
async def test_cu02_registro_verificacion_y_login(client: AsyncClient):
    email = _unique_email()
    await _register_and_verify(client, email)
    response = await login(client, email, "Clave123!")
    assert response.status_code == 200, response.text
    assert response.json()["usuario"]["rol"] == "cliente"


@pytest.mark.asyncio
async def test_cu02_correo_duplicado_en_tenant(client: AsyncClient):
    email = _unique_email()
    payload = {
        "empresa_slug": "demo",
        "nombre": "Duplicado",
        "correo": email,
        "password": "Clave123!",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201, first.text
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "CORREO_DUPLICADO"


@pytest.mark.asyncio
async def test_cu03_perfil_requiere_token(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cu03_perfil_y_actualizacion(client: AsyncClient):
    auth = await login(client, "admin@demo.test", "Admin123!")
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}

    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert "password_hash" not in me.text
    assert me.json()["correo"] == "admin@demo.test"

    updated = await client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"telefono": "71234567"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["telefono"] == "71234567"


@pytest.mark.asyncio
async def test_cu03_cambio_password_revoca_otras_sesiones(client: AsyncClient):
    email = _unique_email()
    await _register_and_verify(client, email, password="Clave123!")

    first = await login(client, email, "Clave123!")
    second = await login(client, email, "Clave123!")
    assert first.status_code == 200
    assert second.status_code == 200

    first_headers = {"Authorization": f"Bearer {first.json()['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second.json()['access_token']}"}

    changed = await client.post(
        "/api/v1/users/me/password",
        headers=first_headers,
        json={"password_actual": "Clave123!", "password_nueva": "Nueva123!"},
    )
    assert changed.status_code == 200, changed.text

    revoked = await client.get("/api/v1/users/me", headers=second_headers)
    assert revoked.status_code == 401
    assert revoked.json()["detail"]["code"] == "SESION_REVOCADA"

    old_login = await login(client, email, "Clave123!")
    assert old_login.status_code == 401

    new_login = await login(client, email, "Nueva123!")
    assert new_login.status_code == 200, new_login.text


@pytest.mark.asyncio
async def test_cu04_logout_revoca_token(client: AsyncClient):
    auth = await login(client, "admin@demo.test", "Admin123!")
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}

    logout = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200, logout.text

    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 401
    assert me.json()["detail"]["code"] == "SESION_REVOCADA"


@pytest.mark.asyncio
async def test_cu04_refresh_rota_token(client: AsyncClient):
    auth = await login(client, "admin@demo.test", "Admin123!")
    refresh_token = auth.json()["refresh_token"]

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["refresh_token"] != refresh_token

    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused.status_code == 401


@pytest.mark.asyncio
async def test_cu05_auditoria_login_y_flag_superadmin(client: AsyncClient):
    auth = await login(client, "superadmin@fashionstore.test", "Superadmin123!", empresa_slug=None)
    assert auth.status_code == 200
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    await client.post("/api/v1/auth/logout", headers=headers)

    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            """
            SELECT count(*)
              FROM bitacora_auditoria
             WHERE es_accion_superadmin = true
               AND accion IN ('login', 'logout')
               AND endpoint IN ('/api/v1/auth/login', '/api/v1/auth/logout')
            """
        )
    assert count and count >= 1


@pytest.mark.asyncio
async def test_cu05_auditoria_http_request(client: AsyncClient):
    auth = await login(client, "admin@demo.test", "Admin123!")
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200

    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            """
            SELECT count(*)
              FROM bitacora_auditoria
             WHERE entidad = 'http_request'
               AND endpoint = '/api/v1/users/me'
            """
        )
    assert count and count >= 1
