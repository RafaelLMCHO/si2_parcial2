"""Suite E2E integral para los Casos de Uso CU-01 a CU-37.

Incluye dos niveles:
1. Tests offline (`test_e2e_offline_*`): validan el contrato completo en OpenAPI y
   las barreras HTTP/RBAC reales en ASGI (`401`/`403`/`422`, nunca `404` ni `5xx`)
   sin requerir conexión a PostgreSQL.
2. Tests online por rol (`test_e2e_online_*`): recorren el flujo mínimo real por CU
   contra la API y la base de datos semilla utilizando usuarios demo por rol
   (`superadmin`, `administrador`, `cliente`, `cajero/encargado` y modo `offline`).
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
import uuid
from uuid import UUID

from httpx import ASGITransport, AsyncClient
import pytest

import app.api.deps as deps_mod
from app.api.deps import CurrentUser, get_current_user
import app.api.routers.catalogo as catalogo_router
from app.db import get_pool
from app.main import app
import app.middleware.audit as audit_middleware_mod
from app.services.sync_service import SyncService
from tests.conftest import login

BASE = "/api/v1"
DEMO_EMPRESA_ID = "11111111-1111-1111-1111-111111111111"
DEMO_SUCURSAL_ID = "11111111-1111-1111-1111-111111111101"
DEMO_PRENDA_ID = "11111111-1111-1111-1111-111111111501"
DEMO_VARIANTE_ID = "11111111-1111-1111-1111-111111111601"
DEMO_VENTA_ID = "11111111-1111-1111-1111-111111111b01"


# ===========================================================================
# 1. NIVEL OFFLINE (Contratos OpenAPI + Barreras HTTP/RBAC para CU-01..CU-37)
# ===========================================================================

EXPECTED_ROUTES_37_CU: list[tuple[str, str, str]] = [
    # CU-01 a CU-05
    ("CU-01", "POST", f"{BASE}/auth/login"),
    ("CU-01", "POST", f"{BASE}/auth/register-tenant"),
    ("CU-02", "POST", f"{BASE}/auth/register"),
    ("CU-02", "POST", f"{BASE}/auth/verify-email"),
    ("CU-03", "GET", f"{BASE}/users/me"),
    ("CU-03", "PATCH", f"{BASE}/users/me"),
    ("CU-03", "POST", f"{BASE}/users/me/password"),
    ("CU-04", "POST", f"{BASE}/auth/refresh"),
    ("CU-04", "POST", f"{BASE}/auth/logout"),
    ("CU-05", "GET", f"{BASE}/auditoria/logs"),
    # CU-06 a CU-09
    ("CU-06", "GET", f"{BASE}/saas/planes"),
    ("CU-06", "POST", f"{BASE}/saas/planes"),
    ("CU-06", "PUT", f"{BASE}/saas/planes/{{plan_id}}"),
    ("CU-06", "DELETE", f"{BASE}/saas/planes/{{plan_id}}"),
    ("CU-07", "GET", f"{BASE}/mi-suscripcion"),
    ("CU-07", "PUT", f"{BASE}/mi-suscripcion"),
    ("CU-07", "POST", f"{BASE}/mi-suscripcion/cancelar"),
    ("CU-07", "GET", f"{BASE}/saas/empresas/{{empresa_id}}/suscripcion"),
    ("CU-07", "PUT", f"{BASE}/saas/empresas/{{empresa_id}}/suscripcion"),
    ("CU-08", "GET", f"{BASE}/saas/facturas"),
    ("CU-08", "GET", f"{BASE}/saas/facturas/{{factura_id}}/pdf"),
    ("CU-09", "GET", f"{BASE}/saas/metricas"),
    ("CU-09", "GET", f"{BASE}/saas/empresas"),
    ("CU-09", "POST", f"{BASE}/saas/empresas/{{empresa_id}}/suspender"),
    ("CU-09", "POST", f"{BASE}/saas/empresas/{{empresa_id}}/reactivar"),
    # CU-10 a CU-18
    ("CU-10", "GET", f"{BASE}/empleados"),
    ("CU-10", "POST", f"{BASE}/empleados"),
    ("CU-10", "PUT", f"{BASE}/empleados/{{empleado_id}}"),
    ("CU-10", "DELETE", f"{BASE}/empleados/{{empleado_id}}"),
    ("CU-11", "GET", f"{BASE}/sucursales"),
    ("CU-11", "POST", f"{BASE}/sucursales"),
    ("CU-11", "PUT", f"{BASE}/sucursales/{{sucursal_id}}"),
    ("CU-11", "DELETE", f"{BASE}/sucursales/{{sucursal_id}}"),
    ("CU-12", "GET", f"{BASE}/catalogo/admin/prendas"),
    ("CU-12", "POST", f"{BASE}/catalogo/admin/prendas"),
    ("CU-12", "PUT", f"{BASE}/catalogo/admin/prendas/{{prenda_id}}"),
    ("CU-12", "DELETE", f"{BASE}/catalogo/admin/prendas/{{prenda_id}}"),
    ("CU-13", "GET", f"{BASE}/catalogo/prendas"),
    ("CU-13", "GET", f"{BASE}/catalogo/prendas/{{prenda_id}}"),
    ("CU-14", "GET", f"{BASE}/catalogo/auxiliares"),
    ("CU-15", "GET", f"{BASE}/proveedores"),
    ("CU-15", "POST", f"{BASE}/proveedores"),
    ("CU-15", "PUT", f"{BASE}/proveedores/{{proveedor_id}}"),
    ("CU-15", "DELETE", f"{BASE}/proveedores/{{proveedor_id}}"),
    ("CU-16", "GET", f"{BASE}/temporadas-colecciones"),
    ("CU-16", "POST", f"{BASE}/temporadas-colecciones/temporadas"),
    ("CU-16", "POST", f"{BASE}/temporadas-colecciones/colecciones"),
    ("CU-17", "GET", f"{BASE}/inventario"),
    ("CU-17", "POST", f"{BASE}/inventario/movimientos/ingreso"),
    ("CU-17", "POST", f"{BASE}/inventario/movimientos/ajuste"),
    ("CU-17", "POST", f"{BASE}/inventario/transferencias"),
    ("CU-17", "GET", f"{BASE}/inventario/movimientos"),
    ("CU-18", "GET", f"{BASE}/inventario/prendas/{{prenda_id}}/disponibilidad"),
    # CU-19 a CU-24
    ("CU-19", "POST", f"{BASE}/reservas/validar"),
    ("CU-19", "POST", f"{BASE}/reservas"),
    ("CU-20", "GET", f"{BASE}/reservas"),
    ("CU-20", "GET", f"{BASE}/reservas/mis-reservas"),
    ("CU-20", "GET", f"{BASE}/reservas/{{reserva_id}}"),
    ("CU-20", "POST", f"{BASE}/reservas/{{reserva_id}}/cancelar"),
    ("CU-21", "GET", f"{BASE}/reservas/por-preparar"),
    ("CU-21", "POST", f"{BASE}/reservas/{{reserva_id}}/preparar"),
    ("CU-21", "POST", f"{BASE}/reservas/{{reserva_id}}/completar"),
    ("CU-21", "POST", f"{BASE}/reservas/{{reserva_id}}/incidencia"),
    ("CU-22", "GET", f"{BASE}/carrito"),
    ("CU-22", "POST", f"{BASE}/carrito/items"),
    ("CU-22", "PATCH", f"{BASE}/carrito/items/{{item_id}}"),
    ("CU-22", "DELETE", f"{BASE}/carrito/items/{{item_id}}"),
    ("CU-22", "POST", f"{BASE}/checkout/validar"),
    ("CU-22", "POST", f"{BASE}/checkout/ordenes"),
    ("CU-22", "GET", f"{BASE}/checkout/ventas/{{venta_id}}/comprobante"),
    ("CU-23", "GET", f"{BASE}/pos/variantes/barcode/{{codigo}}"),
    ("CU-23", "GET", f"{BASE}/pos/variantes/buscar"),
    ("CU-23", "POST", f"{BASE}/pos/ventas"),
    ("CU-23", "GET", f"{BASE}/pos/ventas/{{venta_id}}/ticket"),
    ("CU-24", "GET", f"{BASE}/pagos"),
    ("CU-24", "POST", f"{BASE}/pagos/intencion"),
    ("CU-24", "GET", f"{BASE}/pagos/{{pago_id}}"),
    ("CU-24", "POST", f"{BASE}/pagos/{{pago_id}}/conciliar"),
    ("CU-24", "POST", f"{BASE}/pagos/{{pago_id}}/reembolsar"),
    ("CU-24", "POST", f"{BASE}/pagos/webhook/stripe"),
    ("CU-24", "GET", f"{BASE}/pagos/ventas/{{venta_id}}/estado-pago"),
    # CU-25 a CU-32
    ("CU-25", "GET", f"{BASE}/sync/catalogo-offline"),
    ("CU-26/28/30/31", "POST", f"{BASE}/sync"),
    ("CU-27", "GET", f"{BASE}/sync/soft-locks"),
    ("CU-27", "POST", f"{BASE}/sync/soft-locks"),
    ("CU-27", "DELETE", f"{BASE}/sync/soft-locks/{{lock_id}}"),
    ("CU-29", "POST", f"{BASE}/sync/validar-qr"),
    ("CU-29", "POST", f"{BASE}/sync/nota-cambio"),
    ("CU-32", "GET", f"{BASE}/sync/conflictos"),
    ("CU-32", "POST", f"{BASE}/sync/conflictos/resolver"),
    # CU-33 a CU-37
    ("CU-33", "GET", f"{BASE}/reportes/convencionales/dashboard"),
    ("CU-33", "GET", f"{BASE}/reportes/convencionales/ventas"),
    ("CU-33", "GET", f"{BASE}/reportes/convencionales/rotacion"),
    ("CU-33", "GET", f"{BASE}/reportes/convencionales/top-prendas"),
    ("CU-34", "POST", f"{BASE}/reportes/ia/consultar"),
    ("CU-34", "POST", f"{BASE}/reportes/ia/exportar"),
    ("CU-35", "GET", f"{BASE}/inteligencia/ml/dashboard"),
    ("CU-35", "GET", f"{BASE}/inteligencia/ml/demanda"),
    ("CU-35", "GET", f"{BASE}/inteligencia/ml/segmentacion"),
    ("CU-35", "POST", f"{BASE}/inteligencia/ml/sintesis-audio"),
    ("CU-36", "GET", f"{BASE}/vestidor/prendas"),
    ("CU-36", "GET", f"{BASE}/vestidor/prendas/{{prenda_id}}"),
    ("CU-36", "GET", f"{BASE}/vestidor/avatar"),
    ("CU-36", "POST", f"{BASE}/vestidor/sesiones"),
    ("CU-36", "PUT", f"{BASE}/vestidor/sesiones/{{sesion_id}}"),
    ("CU-36", "POST", f"{BASE}/vestidor/lucy-session"),
    ("CU-36", "POST", f"{BASE}/vestidor/lucy-prompt"),
    ("CU-37", "GET", f"{BASE}/backups/modulos"),
    ("CU-37", "GET", f"{BASE}/backups/estadisticas"),
    ("CU-37", "GET", f"{BASE}/backups/configuracion"),
    ("CU-37", "PUT", f"{BASE}/backups/configuracion"),
    ("CU-37", "POST", f"{BASE}/backups/configuracion/ejecutar-auto"),
    ("CU-37", "GET", f"{BASE}/backups"),
    ("CU-37", "POST", f"{BASE}/backups"),
    ("CU-37", "GET", f"{BASE}/backups/{{backup_id}}"),
    ("CU-37", "GET", f"{BASE}/backups/{{backup_id}}/download/{{location}}"),
    ("CU-37", "POST", f"{BASE}/backups/{{backup_id}}/sync-cloud"),
    ("CU-37", "POST", f"{BASE}/backups/{{backup_id}}/sync-local"),
    ("CU-37", "POST", f"{BASE}/backups/{{backup_id}}/restaurar"),
    ("CU-37", "DELETE", f"{BASE}/backups/{{backup_id}}"),
]


def test_e2e_offline_openapi_todos_los_37_cu():
    """Offline: verifica que todas las rutas canónicas de CU-01 a CU-37 existan en OpenAPI."""
    schema = app.openapi()
    paths = schema.get("paths", {})
    missing: list[str] = []

    for cu, method, route_path in EXPECTED_ROUTES_37_CU:
        methods_dict = paths.get(route_path)
        if not methods_dict or method.lower() not in methods_dict:
            missing.append(f"[{cu}] {method} {route_path}")

    assert not missing, f"Faltan rutas en OpenAPI: {missing}"


@pytest.mark.asyncio
async def test_e2e_offline_http_guards_y_validaciones_37_cu(monkeypatch):
    """Offline ASGI: ninguna ruta CU-01..CU-37 devuelve 404 ni 5xx ante peticiones inválidas o sin JWT."""
    monkeypatch.setattr(
        audit_middleware_mod,
        "get_settings",
        lambda: SimpleNamespace(audit_enabled=False, trusted_proxies=""),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as asgi:
        # Endpoints públicos: payload vacío -> 422 (validación Pydantic), nunca 404 ni 5xx
        public_invalid_posts = [
            f"{BASE}/auth/login",
            f"{BASE}/auth/register",
            f"{BASE}/auth/register-tenant",
            f"{BASE}/auth/verify-email",
            f"{BASE}/auth/refresh",
        ]
        for url in public_invalid_posts:
            resp = await asgi.post(url, json={})
            assert resp.status_code != 404, f"Endpoint faltante: {url}"
            assert resp.status_code < 500, f"Error 5xx en {url}: {resp.text}"
            assert resp.status_code == 422

        # Consulta catálogo sin slug ni token -> 400 EMPRESA_REQUERIDA (nunca 404 ni 5xx)
        for cat_url in (
            f"{BASE}/catalogo/prendas",
            f"{BASE}/catalogo/prendas/{DEMO_PRENDA_ID}",
            f"{BASE}/catalogo/auxiliares",
        ):
            cat_resp = await asgi.get(cat_url)
            assert cat_resp.status_code == 400, f"{cat_url} devolvió {cat_resp.status_code}: {cat_resp.text}"

        # Header X-Empresa-Slug también se resuelve sin AttributeError (404 si slug no existe)
        @asynccontextmanager
        async def _fake_admin_conn():
            class _Conn:
                async def fetchrow(self, *args, **kwargs):
                    return None

            yield _Conn()

        monkeypatch.setattr(catalogo_router, "admin_connection", _fake_admin_conn)
        hdr_resp = await asgi.get(f"{BASE}/catalogo/prendas", headers={"X-Empresa-Slug": "tienda-inexistente"})
        assert hdr_resp.status_code == 404

        # Endpoints protegidos sin Authorization -> 401/403 (nunca 404 ni 5xx)
        protected_calls = [
            ("GET", f"{BASE}/users/me"),
            ("POST", f"{BASE}/auth/logout"),
            ("GET", f"{BASE}/auditoria/logs"),
            ("GET", f"{BASE}/saas/planes"),
            ("GET", f"{BASE}/saas/facturas"),
            ("GET", f"{BASE}/saas/metricas"),
            ("GET", f"{BASE}/saas/empresas"),
            ("GET", f"{BASE}/mi-suscripcion"),
            ("GET", f"{BASE}/empleados"),
            ("GET", f"{BASE}/sucursales"),
            ("GET", f"{BASE}/catalogo/admin/prendas"),
            ("GET", f"{BASE}/proveedores"),
            ("GET", f"{BASE}/temporadas-colecciones"),
            ("GET", f"{BASE}/inventario"),
            ("GET", f"{BASE}/inventario/prendas/{DEMO_PRENDA_ID}/disponibilidad"),
            ("POST", f"{BASE}/reservas/validar"),
            ("GET", f"{BASE}/reservas/mis-reservas"),
            ("GET", f"{BASE}/reservas/por-preparar"),
            ("POST", f"{BASE}/reservas/{uuid.uuid4()}/completar"),
            ("GET", f"{BASE}/carrito"),
            ("POST", f"{BASE}/checkout/validar"),
            ("GET", f"{BASE}/pos/variantes/buscar"),
            ("GET", f"{BASE}/pagos"),
            ("POST", f"{BASE}/pagos/intencion"),
            ("GET", f"{BASE}/sync/catalogo-offline"),
            ("GET", f"{BASE}/sync/soft-locks"),
            ("POST", f"{BASE}/sync"),
            ("GET", f"{BASE}/sync/conflictos"),
            ("GET", f"{BASE}/reportes/convencionales/dashboard"),
            ("POST", f"{BASE}/reportes/ia/consultar"),
            ("GET", f"{BASE}/inteligencia/ml/dashboard"),
            ("GET", f"{BASE}/vestidor/prendas"),
            ("POST", f"{BASE}/vestidor/lucy-session"),
            ("GET", f"{BASE}/backups"),
        ]
        for method, url in protected_calls:
            resp = await asgi.request(method, url)
            assert resp.status_code != 404, f"Endpoint faltante: {method} {url}"
            assert resp.status_code < 500, f"Error 5xx en {method} {url}: {resp.text}"
            assert resp.status_code in (401, 403), f"{method} {url} devolvió {resp.status_code}"


@pytest.mark.asyncio
async def test_e2e_offline_rbac_cliente_bloqueado_en_rutas_staff(monkeypatch):
    """Offline ASGI: valida que el rol cliente recibe 403 (nunca 404/5xx) en endpoints restringidos."""
    monkeypatch.setattr(
        audit_middleware_mod,
        "get_settings",
        lambda: SimpleNamespace(audit_enabled=False, trusted_proxies=""),
    )

    @asynccontextmanager
    async def _fake_tenant_conn_sin_permisos(_empresa_id, _user_id):
        class _Conn:
            async def fetchval(self, *args, **kwargs):
                return None

        yield _Conn()

    monkeypatch.setattr(deps_mod, "tenant_connection", _fake_tenant_conn_sin_permisos)

    fake_cliente = CurrentUser(
        user_id=str(uuid.uuid4()),
        empresa_id=DEMO_EMPRESA_ID,
        rol="cliente",
        session_id=str(uuid.uuid4()),
    )
    app.dependency_overrides[get_current_user] = lambda: fake_cliente
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as asgi:
            staff_routes = [
                ("GET", f"{BASE}/saas/planes", None),
                ("GET", f"{BASE}/saas/metricas", None),
                ("GET", f"{BASE}/saas/facturas", None),
                ("GET", f"{BASE}/mi-suscripcion", None),
                ("GET", f"{BASE}/auditoria/logs", None),
                ("GET", f"{BASE}/empleados", None),
                ("GET", f"{BASE}/sucursales", None),
                ("GET", f"{BASE}/catalogo/admin/prendas", None),
                ("GET", f"{BASE}/proveedores", None),
                ("GET", f"{BASE}/temporadas-colecciones", None),
                ("GET", f"{BASE}/inventario", None),
                ("GET", f"{BASE}/reservas/por-preparar", None),
                ("POST", f"{BASE}/reservas/{uuid.uuid4()}/completar", {"motivo": "No autorizado"}),
                ("GET", f"{BASE}/pos/variantes/buscar", None),
                ("GET", f"{BASE}/reportes/convencionales/dashboard", None),
                ("GET", f"{BASE}/inteligencia/ml/dashboard", None),
                ("GET", f"{BASE}/backups", None),
            ]
            for method, url, body in staff_routes:
                resp = await asgi.request(method, url, json=body)
                assert resp.status_code != 404, f"Endpoint faltante: {method} {url}"
                assert resp.status_code < 500, f"Error 5xx en {method} {url}: {resp.text}"
                assert resp.status_code == 403, f"RBAC falló en {method} {url}: status={resp.status_code}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ===========================================================================
# 2. NIVEL ONLINE E2E POR ROL (Flujo completo CU-01..CU-37 con PostgreSQL)
# ===========================================================================


def _assert_valid_http(resp, label: str, allowed_statuses: tuple[int, ...] = (200, 201)):
    assert resp.status_code != 404, f"[{label}] Ruta no encontrada (404): {resp.text}"
    assert resp.status_code < 500, f"[{label}] Error 5xx ({resp.status_code}): {resp.text}"
    assert resp.status_code in allowed_statuses, (
        f"[{label}] Status inesperado {resp.status_code}: {resp.text}"
    )


@pytest.mark.asyncio
async def test_e2e_online_superadmin_cu05_cu06_cu07_cu08_cu09_cu37(client: AsyncClient):
    """E2E Superadmin + Ciclo Tenant: CU-01, CU-02, CU-04, CU-05, CU-06, CU-07, CU-08, CU-09, CU-37."""
    # CU-01 & CU-04: Login Superadmin
    sa_login = await login(client, "superadmin@fashionstore.test", "Superadmin123!", empresa_slug=None)
    _assert_valid_http(sa_login, "CU-01 login superadmin", (200,))
    sa_token = sa_login.json()["access_token"]
    sa_refresh = sa_login.json()["refresh_token"]
    sa_headers = {"Authorization": f"Bearer {sa_token}"}

    refreshed = await client.post(f"{BASE}/auth/refresh", json={"refresh_token": sa_refresh})
    _assert_valid_http(refreshed, "CU-04 refresh superadmin", (200,))
    sa_headers = {"Authorization": f"Bearer {refreshed.json()['access_token']}"}

    # CU-05: Logs globales
    logs_res = await client.get(f"{BASE}/auditoria/logs", params={"page": 1, "page_size": 5}, headers=sa_headers)
    _assert_valid_http(logs_res, "CU-05 auditoria logs", (200,))

    # CU-09: Métricas SaaS y empresas
    met_res = await client.get(f"{BASE}/saas/metricas", headers=sa_headers)
    _assert_valid_http(met_res, "CU-09 saas metricas", (200,))
    emp_res = await client.get(f"{BASE}/saas/empresas", headers=sa_headers)
    _assert_valid_http(emp_res, "CU-09 listar empresas", (200,))

    # CU-06: CRUD planes SaaS
    suffix = uuid.uuid4().hex[:6]
    plan_code = f"e2e_{suffix}"
    plan_created = await client.post(
        f"{BASE}/saas/planes",
        headers=sa_headers,
        json={
            "codigo": plan_code,
            "nombre": f"Plan E2E {suffix}",
            "precio_mensual": 299.0,
            "periodo": "mensual",
            "moneda": "BOB",
            "limites": {"sucursales": 3, "usuarios": 15, "productos": 1000, "consultas_ia_mes": 50},
        },
    )
    _assert_valid_http(plan_created, "CU-06 crear plan", (201,))
    plan_id = plan_created.json()["id"]

    # CU-01 / CU-02 / CU-07: Registrar tenant temporal, verificar y cambiar suscripción
    temp_empresa_id: str | None = None
    try:
        reg_ten = await client.post(
            f"{BASE}/auth/register-tenant",
            json={
                "nombre_empresa": f"E2E Boutique {suffix}",
                "nit": f"E2E{suffix}".upper(),
                "telefono": "70001122",
                "direccion": "Av. Prueba 456",
                "nombre_admin": "Admin E2E",
                "email_admin": f"e2eadmin_{suffix}@tenant.test",
                "password": "Password123!",
                "plan_codigo": "basico",
            },
        )
        _assert_valid_http(reg_ten, "CU-01 register-tenant", (201,))
        temp_empresa_id = reg_ten.json()["empresa_id"]
        temp_slug = reg_ten.json()["slug"]
        ver_tok = reg_ten.json()["verification_token"]

        ver_res = await client.post(
            f"{BASE}/auth/verify-email",
            json={"empresa_slug": temp_slug, "token": ver_tok},
        )
        _assert_valid_http(ver_res, "CU-02 verify-email tenant", (200,))

        ten_login = await login(client, f"e2eadmin_{suffix}@tenant.test", "Password123!", empresa_slug=temp_slug)
        _assert_valid_http(ten_login, "CU-01 login nuevo tenant", (200,))
        ten_headers = {"Authorization": f"Bearer {ten_login.json()['access_token']}"}

        # CU-07: Ver y cambiar mi suscripción
        mi_sub = await client.get(f"{BASE}/mi-suscripcion", headers=ten_headers)
        _assert_valid_http(mi_sub, "CU-07 get mi-suscripcion", (200,))
        chg_sub = await client.put(
            f"{BASE}/mi-suscripcion",
            headers=ten_headers,
            json={"plan_codigo": "profesional", "renovacion_auto": False},
        )
        _assert_valid_http(chg_sub, "CU-07 put mi-suscripcion", (200,))
        can_sub = await client.post(
            f"{BASE}/mi-suscripcion/cancelar",
            headers=ten_headers,
            json={"motivo": "Limpieza E2E"},
        )
        _assert_valid_http(can_sub, "CU-07 post mi-suscripcion cancelar", (200,))

        # CU-08: Listar facturas SaaS y descargar PDF
        fac_res = await client.get(f"{BASE}/saas/facturas", headers=sa_headers)
        _assert_valid_http(fac_res, "CU-08 listar facturas", (200,))
        fac_items = fac_res.json() if isinstance(fac_res.json(), list) else fac_res.json().get("items", [])
        factura_id = fac_items[0]["id"] if fac_items else f"FAC-{DEMO_EMPRESA_ID[:8].upper()}"
        pdf_res = await client.get(f"{BASE}/saas/facturas/{factura_id}/pdf", headers=sa_headers)
        _assert_valid_http(pdf_res, "CU-08 descargar factura pdf", (200,))
        assert pdf_res.content.startswith(b"%PDF")

        # CU-06 update & delete plan
        upd_plan = await client.put(
            f"{BASE}/saas/planes/{plan_id}",
            headers=sa_headers,
            json={"nombre": f"Plan E2E Mod {suffix}"},
        )
        _assert_valid_http(upd_plan, "CU-06 update plan", (200,))

        # CU-37: Backups módulos y listado superadmin
        mod_res = await client.get(f"{BASE}/backups/modulos", headers=sa_headers)
        _assert_valid_http(mod_res, "CU-37 modulos", (200,))
        bkp_list = await client.get(f"{BASE}/backups", headers=sa_headers)
        _assert_valid_http(bkp_list, "CU-37 listar backups", (200,))
    finally:
        await client.delete(f"{BASE}/saas/planes/{plan_id}", headers=sa_headers)
        if temp_empresa_id:
            async with get_pool().acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SET LOCAL session_replication_role = 'replica'")
                    await conn.execute("DELETE FROM empresa WHERE id = $1", UUID(temp_empresa_id))
        await client.post(f"{BASE}/auth/logout", headers=sa_headers)


@pytest.mark.asyncio
async def test_e2e_online_admin_cu10_a_cu17_cu33_cu34_cu35_cu37(client: AsyncClient):
    """E2E Administrador: CU-03, CU-10..CU-17, CU-33, CU-34, CU-35 y CU-37."""
    adm_login = await login(client, "admin@demo.test", "Admin123!")
    _assert_valid_http(adm_login, "CU-01 login admin", (200,))
    headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}
    suffix = uuid.uuid4().hex[:6]

    # CU-03: Perfil propio
    me_res = await client.get(f"{BASE}/users/me", headers=headers)
    _assert_valid_http(me_res, "CU-03 get profile", (200,))

    # CU-10: Empleados
    roles_res = await client.get(f"{BASE}/empleados/roles", headers=headers)
    _assert_valid_http(roles_res, "CU-10 roles", (200,))
    emp_create = await client.post(
        f"{BASE}/empleados",
        headers=headers,
        json={
            "nombre": f"E2E Cajero {suffix}",
            "correo": f"e2e_emp_{suffix}@demo.test",
            "password": "Password123!",
            "rol": "cajero",
            "sucursal_id": DEMO_SUCURSAL_ID,
        },
    )
    _assert_valid_http(emp_create, "CU-10 create empleado", (201,))
    emp_id = emp_create.json()["id"]

    try:
        emp_list = await client.get(f"{BASE}/empleados", headers=headers)
        _assert_valid_http(emp_list, "CU-10 list empleados", (200,))

        # CU-11: Sucursales
        suc_list = await client.get(f"{BASE}/sucursales", headers=headers)
        _assert_valid_http(suc_list, "CU-11 list sucursales", (200,))
        if suc_list.json()["activas"] < suc_list.json()["limite_plan"]:
            suc_new = await client.post(
                f"{BASE}/sucursales",
                headers=headers,
                json={"nombre": f"Sucursal E2E {suffix}", "ciudad_id": 1, "direccion": "Calle Test 10", "es_matriz": False},
            )
            _assert_valid_http(suc_new, "CU-11 create sucursal", (201,))
            await client.delete(f"{BASE}/sucursales/{suc_new.json()['id']}", headers=headers)

        # CU-15: Proveedores
        prov_create = await client.post(
            f"{BASE}/proveedores",
            headers=headers,
            json={"nombre": f"Prov E2E {suffix}", "nit": f"PNIT{suffix}", "correo": f"p{suffix}@demo.test"},
        )
        _assert_valid_http(prov_create, "CU-15 create proveedor", (201,))
        prov_id = prov_create.json()["id"]
        _assert_valid_http(await client.get(f"{BASE}/proveedores", headers=headers), "CU-15 list proveedores", (200,))
        _assert_valid_http(await client.delete(f"{BASE}/proveedores/{prov_id}", headers=headers), "CU-15 delete proveedor", (200,))

        # CU-16: Temporadas y colecciones
        temp_res = await client.post(
            f"{BASE}/temporadas-colecciones/temporadas",
            headers=headers,
            json={"nombre": f"Temp E2E {suffix}", "fecha_inicio": "2026-04-01", "fecha_fin": "2026-09-30"},
        )
        _assert_valid_http(temp_res, "CU-16 create temporada", (201,))
        col_res = await client.post(
            f"{BASE}/temporadas-colecciones/colecciones",
            headers=headers,
            json={"nombre": f"Col E2E {suffix}", "anio": 2026},
        )
        _assert_valid_http(col_res, "CU-16 create coleccion", (201,))
        _assert_valid_http(await client.get(f"{BASE}/temporadas-colecciones", headers=headers), "CU-16 list", (200,))
        await client.delete(f"{BASE}/temporadas-colecciones/temporadas/{temp_res.json()['id']}", headers=headers)
        await client.delete(f"{BASE}/temporadas-colecciones/colecciones/{col_res.json()['id']}", headers=headers)

        # CU-12 / CU-13 / CU-14: Catálogo admin + auxiliares
        aux_res = await client.get(f"{BASE}/catalogo/auxiliares", params={"empresa_slug": "demo"})
        _assert_valid_http(aux_res, "CU-14 auxiliares", (200,))
        aux = aux_res.json()
        prenda_create = await client.post(
            f"{BASE}/catalogo/admin/prendas",
            headers=headers,
            json={
                "codigo": f"E2E-{suffix}",
                "nombre": f"Prenda E2E {suffix}",
                "precio_base": 150.0,
                "categoria_id": aux["categorias"][0]["id"],
                "genero": "unisex",
                "variantes": [
                    {
                        "talla_id": aux["tallas"][0]["id"],
                        "color_id": aux["colores"][0]["id"],
                        "sku": f"SKUE2E-{suffix}",
                        "precio_venta": 150.0,
                        "costo": 75.0,
                    }
                ],
            },
        )
        _assert_valid_http(prenda_create, "CU-12 create prenda", (201,))
        prenda_id = prenda_create.json()["id"]
        _assert_valid_http(await client.get(f"{BASE}/catalogo/admin/prendas", headers=headers), "CU-12 list admin", (200,))
        await client.delete(f"{BASE}/catalogo/admin/prendas/{prenda_id}", headers=headers)

        # CU-17: Inventario (+1 ingreso y -1 ajuste compensatorio)
        _assert_valid_http(await client.get(f"{BASE}/inventario", headers=headers), "CU-17 inventario", (200,))
        _assert_valid_http(
            await client.post(
                f"{BASE}/inventario/movimientos/ingreso",
                headers=headers,
                json={"sucursal_id": DEMO_SUCURSAL_ID, "items": [{"variante_id": DEMO_VARIANTE_ID, "cantidad": 1}], "motivo": "E2E ingreso"},
            ),
            "CU-17 ingreso",
            (200,),
        )
        _assert_valid_http(
            await client.post(
                f"{BASE}/inventario/movimientos/ajuste",
                headers=headers,
                json={"sucursal_id": DEMO_SUCURSAL_ID, "variante_id": DEMO_VARIANTE_ID, "cantidad": -1, "motivo": "E2E cierre"},
            ),
            "CU-17 ajuste",
            (200,),
        )
        _assert_valid_http(await client.get(f"{BASE}/inventario/movimientos", headers=headers), "CU-17 kardex", (200,))

        # CU-33: Reportes convencionales
        _assert_valid_http(await client.get(f"{BASE}/reportes/convencionales/dashboard", headers=headers), "CU-33 dashboard", (200,))
        _assert_valid_http(await client.get(f"{BASE}/reportes/convencionales/ventas", headers=headers), "CU-33 ventas", (200,))
        _assert_valid_http(await client.get(f"{BASE}/reportes/convencionales/rotacion", headers=headers), "CU-33 rotacion", (200,))
        _assert_valid_http(await client.get(f"{BASE}/reportes/convencionales/top-prendas", headers=headers), "CU-33 top", (200,))

        # CU-34: Reporte generativo IA (whitelist BR-08 + rechazo SQL + exportación)
        ia_res = await client.post(
            f"{BASE}/reportes/ia/consultar",
            headers=headers,
            json={"prompt": "Mostrame las ventas agrupadas por sucursal", "canal": "texto"},
        )
        _assert_valid_http(ia_res, "CU-34 ia consultar", (200,))
        ia_rej = await client.post(
            f"{BASE}/reportes/ia/consultar",
            headers=headers,
            json={"prompt": "DROP TABLE venta", "canal": "texto"},
        )
        _assert_valid_http(ia_rej, "CU-34 ia br-08 rechazo", (400,))
        exp_res = await client.post(
            f"{BASE}/reportes/ia/exportar",
            headers=headers,
            json={
                "tipo_reporte": "ventas_por_sucursal",
                "formato": "xlsx",
                "titulo": "E2E Export",
                "columnas": ["Sucursal", "Monto"],
                "filas": [{"sucursal": "Centro", "monto": 100.0}],
            },
        )
        _assert_valid_http(exp_res, "CU-34 exportar xlsx", (200,))

        # CU-35: Machine Learning & TTS
        _assert_valid_http(await client.get(f"{BASE}/inteligencia/ml/dashboard?demo=true", headers=headers), "CU-35 ml dashboard", (200,))
        _assert_valid_http(await client.get(f"{BASE}/inteligencia/ml/demanda?demo=true", headers=headers), "CU-35 ml demanda", (200,))
        _assert_valid_http(await client.get(f"{BASE}/inteligencia/ml/segmentacion?demo=true", headers=headers), "CU-35 ml segmentacion", (200,))
        _assert_valid_http(
            await client.post(f"{BASE}/inteligencia/ml/sintesis-audio", headers=headers, json={"texto": "Resumen E2E"}),
            "CU-35 tts",
            (200,),
        )

        # CU-37: Backups admin
        _assert_valid_http(await client.get(f"{BASE}/backups/estadisticas", headers=headers), "CU-37 stats", (200,))
        bkp_res = await client.post(
            f"{BASE}/backups",
            headers=headers,
            json={"nombre": f"E2E_Bkp_{suffix}", "alcance": "empresa", "formato": "json", "destino": "local", "modulos": ["catalogo"]},
        )
        _assert_valid_http(bkp_res, "CU-37 create backup", (201,))
        await client.delete(f"{BASE}/backups/{bkp_res.json()['id']}", headers=headers)
    finally:
        await client.delete(f"{BASE}/empleados/{emp_id}", headers=headers)


@pytest.mark.asyncio
async def test_e2e_online_cliente_cu13_cu14_cu18_cu19_cu20_cu22_cu36(client: AsyncClient):
    """E2E Cliente: CU-13, CU-14, CU-18, CU-19, CU-20, CU-22 y CU-36."""
    cli_login = await login(client, "cliente@demo.test", "Cliente123!")
    _assert_valid_http(cli_login, "CU-01 login cliente", (200,))
    token = cli_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # CU-13 / CU-14: Catálogo y filtros
    _assert_valid_http(
        await client.get(f"{BASE}/catalogo/prendas", params={"empresa_slug": "demo", "search": "Vestido"}),
        "CU-13/14 listar catalogo",
        (200,),
    )
    _assert_valid_http(
        await client.get(f"{BASE}/catalogo/prendas/{DEMO_PRENDA_ID}", params={"empresa_slug": "demo"}),
        "CU-13 detalle prenda",
        (200,),
    )

    # CU-18: Disponibilidad canónica
    _assert_valid_http(
        await client.get(f"{BASE}/inventario/prendas/{DEMO_PRENDA_ID}/disponibilidad", headers=headers),
        "CU-18 disponibilidad canonica",
        (200,),
    )

    # CU-19 / CU-20: Validar reserva, crear, listar mis-reservas y cancelar
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    rsv_payload = {
        "sucursal_id": DEMO_SUCURSAL_ID,
        "fecha_visita": fecha_futura,
        "items": [{"variante_id": DEMO_VARIANTE_ID, "cantidad": 1}],
    }
    _assert_valid_http(await client.post(f"{BASE}/reservas/validar", headers=headers, json=rsv_payload), "CU-19 validar", (200,))
    rsv_created = await client.post(
        f"{BASE}/reservas",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json=rsv_payload,
    )
    _assert_valid_http(rsv_created, "CU-19 crear reserva", (201,))
    rsv_id = rsv_created.json()["id"]

    _assert_valid_http(await client.get(f"{BASE}/reservas/mis-reservas", headers=headers), "CU-20 mis-reservas", (200,))
    _assert_valid_http(await client.get(f"{BASE}/reservas/{rsv_id}", headers=headers), "CU-20 detalle reserva", (200,))
    _assert_valid_http(
        await client.post(f"{BASE}/reservas/{rsv_id}/cancelar", headers=headers, json={"motivo": "Prueba E2E"}),
        "CU-20 cancelar reserva",
        (200,),
    )

    # CU-22: Carrito y Checkout
    _assert_valid_http(
        await client.post(f"{BASE}/carrito/items", headers=headers, json={"variante_id": DEMO_VARIANTE_ID, "cantidad": 1}),
        "CU-22 add carrito",
        (200,),
    )
    _assert_valid_http(await client.get(f"{BASE}/carrito", headers=headers), "CU-22 get carrito", (200,))
    _assert_valid_http(
        await client.post(f"{BASE}/checkout/validar", headers=headers, json={"tipo_entrega": "recojo", "sucursal_id": DEMO_SUCURSAL_ID}),
        "CU-22 validar checkout",
        (200,),
    )
    orden = await client.post(
        f"{BASE}/checkout/ordenes",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"tipo_entrega": "recojo", "sucursal_id": DEMO_SUCURSAL_ID},
    )
    _assert_valid_http(orden, "CU-22 crear orden", (201,))
    _assert_valid_http(
        await client.get(f"{BASE}/checkout/ventas/{DEMO_VENTA_ID}/comprobante", headers=headers),
        "CU-22 comprobante",
        (200,),
    )

    # CU-36: Vestidor virtual AR & Decart Lucy VTON (503 explícito aceptado si falta DECART_API_KEY, nunca 500)
    prendas_ar = await client.get(f"{BASE}/vestidor/prendas", headers=headers)
    _assert_valid_http(prendas_ar, "CU-36 prendas ar", (200,))
    _assert_valid_http(await client.get(f"{BASE}/vestidor/avatar", headers=headers), "CU-36 avatar", (200,))
    _assert_valid_http(
        await client.post(
            f"{BASE}/vestidor/lucy-prompt",
            headers=headers,
            json={"prenda_id": DEMO_PRENDA_ID, "color_nombre": "Negro", "talla": "M"},
        ),
        "CU-36 lucy-prompt",
        (200,),
    )
    lucy_sess = await client.post(f"{BASE}/vestidor/lucy-session", headers=headers)
    _assert_valid_http(lucy_sess, "CU-36 lucy-session", (200, 503))
    if prendas_ar.json():
        ar_p_id = prendas_ar.json()[0]["prenda_id"]
        ses_res = await client.post(f"{BASE}/vestidor/sesiones", headers=headers, json={"prenda_id": ar_p_id})
        _assert_valid_http(ses_res, "CU-36 iniciar sesion", (200,))
        _assert_valid_http(
            await client.put(
                f"{BASE}/vestidor/sesiones/{ses_res.json()['sesion_id']}",
                headers=headers,
                json={"estado": "completada"},
            ),
            "CU-36 finalizar sesion",
            (200,),
        )


@pytest.mark.asyncio
async def test_e2e_online_cajero_encargado_cu21_cu23_cu24(client: AsyncClient):
    """E2E Cajero/Encargado: CU-21 (preparar/completar reserva), CU-23 (POS) y CU-24 (pagos/reembolso)."""
    adm_login = await login(client, "admin@demo.test", "Admin123!")
    _assert_valid_http(adm_login, "login admin", (200,))
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    cli_login = await login(client, "cliente@demo.test", "Cliente123!")
    _assert_valid_http(cli_login, "login cliente", (200,))
    cli_headers = {"Authorization": f"Bearer {cli_login.json()['access_token']}"}

    # CU-21: Cliente crea reserva -> Encargado/Admin prepara y completa
    fecha_futura = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    rsv = await client.post(
        f"{BASE}/reservas",
        headers={**cli_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"sucursal_id": DEMO_SUCURSAL_ID, "fecha_visita": fecha_futura, "items": [{"variante_id": DEMO_VARIANTE_ID, "cantidad": 1}]},
    )
    _assert_valid_http(rsv, "CU-21 crear reserva", (201,))
    rsv_id = rsv.json()["id"]

    _assert_valid_http(await client.get(f"{BASE}/reservas/por-preparar", headers=adm_headers), "CU-21 por-preparar", (200,))
    _assert_valid_http(
        await client.post(f"{BASE}/reservas/{rsv_id}/preparar", headers=adm_headers, json={"probador": "Probador E2E"}),
        "CU-21 preparar",
        (200,),
    )
    _assert_valid_http(
        await client.post(f"{BASE}/reservas/{rsv_id}/completar", headers=adm_headers, json={"motivo": "Completada E2E"}),
        "CU-21 completar",
        (200,),
    )

    # CU-23: Crear cajero temporal para probar POS en mostrador
    suffix = uuid.uuid4().hex[:6]
    cajero_mail = f"e2ecajero_{suffix}@demo.test"
    cajero_emp = await client.post(
        f"{BASE}/empleados",
        headers=adm_headers,
        json={"nombre": f"Cajero {suffix}", "correo": cajero_mail, "password": "Password123!", "rol": "cajero", "sucursal_id": DEMO_SUCURSAL_ID},
    )
    _assert_valid_http(cajero_emp, "CU-23 crear cajero temporal", (201,))
    cajero_emp_id = cajero_emp.json()["id"]

    try:
        caj_login = await login(client, cajero_mail, "Password123!")
        _assert_valid_http(caj_login, "CU-23 login cajero", (200,))
        caj_headers = {"Authorization": f"Bearer {caj_login.json()['access_token']}"}

        _assert_valid_http(await client.get(f"{BASE}/pos/variantes/barcode/FS0001", headers=caj_headers), "CU-23 barcode", (200,))
        _assert_valid_http(await client.get(f"{BASE}/pos/variantes/buscar", params={"q": "Vestido"}, headers=caj_headers), "CU-23 buscar", (200,))
        pos_venta = await client.post(
            f"{BASE}/pos/ventas",
            headers=caj_headers,
            json={
                "idempotency_key": str(uuid.uuid4()),
                "items": [{"variante_id": DEMO_VARIANTE_ID, "cantidad": 1}],
                "cliente": {"tipo": "consumidor_final"},
                "pago": {"metodo": "efectivo", "monto_recibido": 200.0},
            },
        )
        _assert_valid_http(pos_venta, "CU-23 venta pos", (200,))
        _assert_valid_http(await client.get(f"{BASE}/pos/ventas/{pos_venta.json()['venta_id']}/ticket", headers=caj_headers), "CU-23 ticket", (200,))
    finally:
        await client.delete(f"{BASE}/empleados/{cajero_emp_id}", headers=adm_headers)

    # CU-24: Flujo completo de pagos (orden -> intención -> webhook -> listar -> reembolso)
    _assert_valid_http(
        await client.post(f"{BASE}/carrito/items", headers=cli_headers, json={"variante_id": DEMO_VARIANTE_ID, "cantidad": 1}),
        "CU-24 add item",
        (200,),
    )
    orden = await client.post(
        f"{BASE}/checkout/ordenes",
        headers={**cli_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"tipo_entrega": "recojo", "sucursal_id": DEMO_SUCURSAL_ID},
    )
    _assert_valid_http(orden, "CU-24 crear orden", (201,))
    venta_id = orden.json()["venta_id"]

    intencion = await client.post(
        f"{BASE}/pagos/intencion",
        headers={**cli_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"venta_id": venta_id},
    )
    _assert_valid_http(intencion, "CU-24 crear intencion", (200,))
    pago_id = intencion.json()["pago_id"]

    _assert_valid_http(await client.get(f"{BASE}/pagos/ventas/{venta_id}/estado-pago", headers=cli_headers), "CU-24 estado pago", (200,))

    wh = await client.post(
        f"{BASE}/pagos/webhook/stripe",
        json={
            "id": f"evt_e2e_{uuid.uuid4().hex[:10]}",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_e2e_mock", "latest_charge": "ch_e2e_mock", "metadata": {"empresa_id": DEMO_EMPRESA_ID, "venta_id": venta_id, "pago_id": pago_id}}},
        },
    )
    _assert_valid_http(wh, "CU-24 webhook stripe", (200,))
    _assert_valid_http(await client.get(f"{BASE}/pagos", headers=adm_headers), "CU-24 listar pagos", (200,))
    _assert_valid_http(await client.get(f"{BASE}/pagos/{pago_id}", headers=adm_headers), "CU-24 detalle pago", (200,))
    _assert_valid_http(
        await client.post(f"{BASE}/pagos/{pago_id}/reembolsar", headers=adm_headers, json={"motivo": "Reembolso E2E"}),
        "CU-24 reembolsar",
        (200,),
    )


@pytest.mark.asyncio
async def test_e2e_online_sync_cu25_a_cu32(client: AsyncClient):
    """E2E Offline & Sync: CU-25, CU-26, CU-27, CU-28, CU-29, CU-30, CU-31 y CU-32."""
    adm_login = await login(client, "admin@demo.test", "Admin123!")
    _assert_valid_http(adm_login, "login admin offline sync", (200,))
    headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # CU-25: Descargar catálogo offline
    cat_off = await client.get(f"{BASE}/sync/catalogo-offline", headers=headers)
    _assert_valid_http(cat_off, "CU-25 catalogo-offline", (200,))

    # CU-27: Soft-locks (crear, listar con TTL y liberar manualmente)
    sl_create = await client.post(
        f"{BASE}/sync/soft-locks",
        headers=headers,
        json={"sucursal_id": DEMO_SUCURSAL_ID, "variante_id": DEMO_VARIANTE_ID, "cantidad": 1, "dispositivo_id": "E2E-DEV", "ttl_minutos": 30},
    )
    _assert_valid_http(sl_create, "CU-27 crear soft-lock", (200,))
    lock_id = sl_create.json()["id"]
    sl_list = await client.get(f"{BASE}/sync/soft-locks", headers=headers)
    _assert_valid_http(sl_list, "CU-27 listar soft-locks", (200,))
    assert any(item["id"] == lock_id and item["ttl_restante_segundos"] > 0 for item in sl_list.json())
    sl_del = await client.delete(f"{BASE}/sync/soft-locks/{lock_id}", headers=headers)
    _assert_valid_http(sl_del, "CU-27 liberar soft-lock", (200,))
    assert sl_del.json()["liberado"] is True

    # CU-29: Validar QR HMAC y procesar nota de cambio
    sync_helper = SyncService(None)  # type: ignore[arg-type]
    qr_payload = {
        "uuid": str(uuid.uuid4()),
        "fecha_hora_local": datetime.now(timezone.utc).isoformat(),
        "total": 100.0,
        "usuario_id": "11111111-1111-1111-1111-111111111301",
    }
    qr_payload["firma"] = sync_helper.generar_firma_qr_ticket(qr_payload)
    qr_val = await client.post(f"{BASE}/sync/validar-qr", headers=headers, json={"qr_data": json.dumps(qr_payload)})
    _assert_valid_http(qr_val, "CU-29 validar-qr", (200,))
    assert qr_val.json()["valido"] is True

    nota = await client.post(
        f"{BASE}/sync/nota-cambio",
        headers=headers,
        json={
            "sucursal_id": DEMO_SUCURSAL_ID,
            "variante_devuelta_id": DEMO_VARIANTE_ID,
            "variante_nueva_id": DEMO_VARIANTE_ID,
            "cantidad": 1,
            "motivo": "Cambio E2E",
            "qr_firma": qr_payload["firma"],
        },
    )
    _assert_valid_http(nota, "CU-29 nota-cambio", (200,))

    # CU-26, CU-28, CU-30, CU-31: Sincronizar lote idempotente
    op_id = str(uuid.uuid4())
    batch_res = await client.post(
        f"{BASE}/sync",
        headers=headers,
        json={
            "dispositivo_id": "E2E-DEV",
            "operaciones": [
                {
                    "id": op_id,
                    "tipo": "venta_offline",
                    "sucursal_id": DEMO_SUCURSAL_ID,
                    "dispositivo_id": "E2E-DEV",
                    "payload": {"total": 100.0, "lineas": [{"variante_id": DEMO_VARIANTE_ID, "cantidad": 1, "precio_unitario": 100.0}]},
                    "creada_en": datetime.now(timezone.utc).isoformat(),
                    "idempotency_key": f"E2E-SYNC-{op_id}",
                }
            ],
        },
    )
    _assert_valid_http(batch_res, "CU-26/28/30/31 batch sync", (200,))

    # CU-32: Conflictos de sincronización
    conf_op_id = str(uuid.uuid4())
    await client.post(
        f"{BASE}/sync",
        headers=headers,
        json={
            "dispositivo_id": "E2E-DEV",
            "operaciones": [
                {
                    "id": conf_op_id,
                    "tipo": "venta_offline",
                    "sucursal_id": DEMO_SUCURSAL_ID,
                    "dispositivo_id": "E2E-DEV",
                    "payload": {"total": 9999900.0, "lineas": [{"variante_id": DEMO_VARIANTE_ID, "cantidad": 99999, "precio_unitario": 100.0}]},
                    "creada_en": datetime.now(timezone.utc).isoformat(),
                    "idempotency_key": f"E2E-CONF-{conf_op_id}",
                }
            ],
        },
    )
    conf_list = await client.get(f"{BASE}/sync/conflictos", headers=headers)
    _assert_valid_http(conf_list, "CU-32 listar conflictos", (200,))
    if conf_list.json():
        conf_id = conf_list.json()[0]["id"]
        res_conf = await client.post(
            f"{BASE}/sync/conflictos/resolver",
            headers=headers,
            json={"operacion_id": conf_id, "decision": "rechazar", "motivo": "Resuelto E2E"},
        )
        _assert_valid_http(res_conf, "CU-32 resolver conflicto", (200,))
