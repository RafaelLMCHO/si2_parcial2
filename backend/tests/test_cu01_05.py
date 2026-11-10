from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.api.deps import CurrentUser
from app.controller.cu05_auditoria_logs_controller import CU05AuditoriaLogsController
from app.db import get_pool
from app.schemas.auditoria import AuditLogListResponse
from app.services import auditoria_service
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


@pytest.mark.asyncio
async def test_cu01_register_tenant_y_duplicados(client: AsyncClient):
    """CU-01: Alta publica de empresa/inquilino con verificacion, login y validacion de duplicados."""
    suffix = uuid4().hex[:8]
    nit = f"TEN{suffix}".upper()
    correo_admin = f"owner{suffix}@tenant.test"
    payload = {
        "nombre_empresa": f"Boutique {suffix}",
        "nit": nit,
        "telefono": "70001234",
        "direccion": "Av. Comercio 100",
        "nombre_admin": "Dueno Tenant",
        "email_admin": correo_admin,
        "password": "Password123!",
        "plan_codigo": "basico",
    }
    resp = await client.post("/api/v1/auth/register-tenant", json=payload)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    empresa_id = created["empresa_id"]
    slug = created["slug"]
    assert created["email_verificado"] is False
    assert created["verification_token"]

    try:
        verify = await client.post(
            "/api/v1/auth/verify-email",
            json={"empresa_slug": slug, "token": created["verification_token"]},
        )
        assert verify.status_code == 200, verify.text

        logged = await login(client, correo_admin, "Password123!", empresa_slug=slug)
        assert logged.status_code == 200, logged.text
        assert logged.json()["usuario"]["rol"] == "administrador"

        dup_nit = {
            **payload,
            "nombre_empresa": f"Otra {suffix}",
            "email_admin": f"otro{suffix}@tenant.test",
        }
        conflict_nit = await client.post("/api/v1/auth/register-tenant", json=dup_nit)
        assert conflict_nit.status_code == 409, conflict_nit.text
        assert conflict_nit.json()["detail"]["code"] == "NIT_DUPLICADO"

        dup_mail = {
            **payload,
            "nombre_empresa": f"OtraMail {suffix}",
            "nit": f"OTR{suffix}".upper(),
        }
        conflict_mail = await client.post("/api/v1/auth/register-tenant", json=dup_mail)
        assert conflict_mail.status_code == 409, conflict_mail.text
        assert conflict_mail.json()["detail"]["code"] == "CORREO_ADMIN_DUPLICADO"
    finally:
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SET LOCAL session_replication_role = 'replica'")
                await conn.execute("DELETE FROM empresa WHERE id = $1", UUID(empresa_id))


@pytest.mark.asyncio
async def test_cu05_auditoria_logs_filtros_paginacion_y_aislamiento(client: AsyncClient):
    """CU-05: Consulta paginada de bitacora_auditoria con filtros y aislamiento por empresa."""
    admin_auth = await login(client, "admin@demo.test", "Admin123!")
    assert admin_auth.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_auth.json()['access_token']}"}

    logs = await client.get(
        "/api/v1/auditoria/logs",
        params={"page": 1, "page_size": 5, "accion": "login"},
        headers=admin_headers,
    )
    assert logs.status_code == 200, logs.text
    body = logs.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total"] >= 1
    assert all(str(item["empresa_id"]) == DEMO_EMPRESA for item in body["items"])

    other_tenant = await client.get(
        "/api/v1/auditoria/logs",
        params={"empresa_id": str(uuid4())},
        headers=admin_headers,
    )
    assert other_tenant.status_code == 403
    assert other_tenant.json()["detail"]["code"] == "ACCESO_DENEGADO"

    cli_auth = await login(client, "cliente@demo.test", "Cliente123!")
    cli_headers = {"Authorization": f"Bearer {cli_auth.json()['access_token']}"}
    cli_res = await client.get("/api/v1/auditoria/logs", headers=cli_headers)
    assert cli_res.status_code == 403

    sa_auth = await login(client, "superadmin@fashionstore.test", "Superadmin123!", empresa_slug=None)
    sa_headers = {"Authorization": f"Bearer {sa_auth.json()['access_token']}"}
    sa_logs = await client.get(
        "/api/v1/auditoria/logs",
        params={"entidad": "sesion", "page_size": 5},
        headers=sa_headers,
    )
    assert sa_logs.status_code == 200, sa_logs.text
    assert sa_logs.json()["total"] >= 1


@pytest.mark.asyncio
async def test_cu05_controller_listar_logs_conn_offline():
    """CU-05 (offline): Valida filtros SQL, paginacion y mapeo de bitacora_auditoria sin BD."""
    emp_id = uuid4()
    usr_id = uuid4()
    ent_id = uuid4()
    now = datetime.now(timezone.utc)

    class FakeAuditConn:
        def __init__(self):
            self.queries = []

        async def fetchval(self, sql, *args):
            self.queries.append((sql, args))
            return 1

        async def fetch(self, sql, *args):
            self.queries.append((sql, args))
            return [
                {
                    "id": 42,
                    "empresa_id": emp_id,
                    "empresa_afectada_id": None,
                    "usuario_id": usr_id,
                    "usuario_nombre": "Admin Demo",
                    "usuario_correo": "admin@demo.test",
                    "actor_tipo": "usuario",
                    "accion": "insert",
                    "entidad": "venta",
                    "entidad_id": ent_id,
                    "datos_antes": None,
                    "datos_despues": '{"total": 150}',
                    "ip": "127.0.0.1",
                    "ocurrido_en": now,
                    "es_accion_superadmin": False,
                    "metodo": "POST",
                    "endpoint": "/api/v1/pos/ventas",
                    "parametros": {"canal": "POS"},
                }
            ]

    conn = FakeAuditConn()
    res = await CU05AuditoriaLogsController.listar_logs_conn(
        conn,
        empresa_id=str(emp_id),
        usuario_id=str(usr_id),
        accion="insert",
        entidad="venta",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        page=2,
        page_size=10,
    )
    parsed = AuditLogListResponse(**res)
    assert parsed.total == 1
    assert parsed.page == 2
    assert parsed.page_size == 10
    assert len(parsed.items) == 1
    assert parsed.items[0].accion == "insert"
    assert parsed.items[0].modulo == "venta"
    assert parsed.items[0].datos_despues == {"total": 150}
    assert any("bitacora_auditoria" in q[0] and "LIMIT" in q[0] for q in conn.queries)


@pytest.mark.asyncio
async def test_cu05_auditoria_service_aislamiento_offline():
    """CU-05 (offline): Administrador de empresa no puede consultar auditoria de otro tenant."""
    current = CurrentUser(
        user_id=str(uuid4()),
        empresa_id=DEMO_EMPRESA,
        rol="administrador",
        session_id=str(uuid4()),
    )
    with pytest.raises(HTTPException) as exc:
        await auditoria_service.listar_logs(current=current, empresa_id=str(uuid4()))
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "ACCESO_DENEGADO"
