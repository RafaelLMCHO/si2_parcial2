import pytest
from httpx import AsyncClient

from tests.conftest import login


@pytest.mark.asyncio
async def test_cu37_admin_crear_backup_manual_personalizado(client: AsyncClient):
    # 1. Login como Admin de tenant demo
    login_res = await login(client, "admin@demo.test", "Admin123!", empresa_slug="demo")
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Consultar módulos disponibles
    modulos_res = await client.get("/api/v1/backups/modulos", headers=headers)
    assert modulos_res.status_code == 200
    modulos = modulos_res.json()
    assert len(modulos) >= 5
    mod_ids = [m["id"] for m in modulos]
    assert "catalogo" in mod_ids
    assert "inventario" in mod_ids
    assert "ventas" in mod_ids
    # El admin no debe ver saas_global
    assert "saas_global" not in mod_ids

    # 3. Crear backup manual personalizado (Catálogo e Inventario, formato JSON, destino ambos)
    payload = {
        "nombre": "Test_Backup_Admin_Manual",
        "descripcion": "Backup de prueba para inventario y catálogo",
        "alcance": "empresa",
        "formato": "json",
        "destino": "ambos",
        "modulos": ["catalogo", "inventario"],
        "incluir_auditoria": False,
    }
    create_res = await client.post("/api/v1/backups", json=payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    backup = create_res.json()

    assert backup["nombre"] == "Test_Backup_Admin_Manual"
    assert backup["tipo"] == "manual"
    assert backup["alcance"] == "empresa"
    assert backup["formato"] == "json"
    assert backup["guardado_local"] is True
    assert backup["guardado_nube"] is True
    assert backup["ruta_local"] is not None
    assert "s3://fashionstore-backups/cloud" in backup["url_nube"]
    assert backup["checksum_sha256"] is not None
    assert backup["total_registros"] >= 0

    backup_id = backup["id"]

    # 4. Obtener detalle de backup
    detail_res = await client.get(f"/api/v1/backups/{backup_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == backup_id

    # 5. Descargar archivo local
    down_local = await client.get(f"/api/v1/backups/{backup_id}/download/local", headers=headers)
    assert down_local.status_code == 200
    assert len(down_local.content) > 0
    assert down_local.headers.get("X-Storage-Location") == "local"

    # 6. Descargar archivo desde la nube
    down_cloud = await client.get(f"/api/v1/backups/{backup_id}/download/cloud", headers=headers)
    assert down_cloud.status_code == 200
    assert len(down_cloud.content) > 0
    assert down_cloud.headers.get("X-Storage-Location") == "cloud"


@pytest.mark.asyncio
async def test_cu37_superadmin_backup_global_y_modulos(client: AsyncClient):
    # 1. Login como Superadmin
    login_res = await login(client, "superadmin@fashionstore.test", "Superadmin123!", empresa_slug=None)
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Módulos disponibles para superadmin deben incluir saas_global
    modulos_res = await client.get("/api/v1/backups/modulos", headers=headers)
    assert modulos_res.status_code == 200
    mod_ids = [m["id"] for m in modulos_res.json()]
    assert "saas_global" in mod_ids

    # 3. Crear backup global en formato SQL guardado en la nube y localhost
    payload = {
        "nombre": "Test_Backup_Superadmin_Global_SQL",
        "descripcion": "Backup global del sistema SaaS en SQL",
        "alcance": "global",
        "formato": "sql",
        "destino": "ambos",
        "modulos": ["saas_global", "usuarios"],
    }
    create_res = await client.post("/api/v1/backups", json=payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    backup = create_res.json()
    assert backup["alcance"] == "global"
    assert backup["formato"] == "sql"
    assert backup["guardado_nube"] is True
    assert backup["guardado_local"] is True


@pytest.mark.asyncio
async def test_cu37_configuracion_backup_automatico(client: AsyncClient):
    login_res = await login(client, "admin@demo.test", "Admin123!", empresa_slug="demo")
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Obtener configuración actual
    get_cfg = await client.get("/api/v1/backups/configuracion", headers=headers)
    assert get_cfg.status_code == 200
    cfg = get_cfg.json()
    assert "frecuencia" in cfg

    # 2. Actualizar configuración de backup automático
    update_payload = {
        "activo": True,
        "frecuencia": "cada_6_horas",
        "hora_ejecucion": "03:30",
        "dia_semana": 1,
        "destino": "ambos",
        "formato": "json",
        "tablas": ["catalogo", "inventario", "ventas"],
        "retencion_dias": 15,
    }
    put_cfg = await client.put("/api/v1/backups/configuracion", json=update_payload, headers=headers)
    assert put_cfg.status_code == 200, put_cfg.text
    new_cfg = put_cfg.json()
    assert new_cfg["activo"] is True
    assert new_cfg["frecuencia"] == "cada_6_horas"
    assert new_cfg["proxima_ejecucion"] is not None

    # 3. Disparar ejecución automática inmediata para probar el worker
    exec_res = await client.post("/api/v1/backups/configuracion/ejecutar-auto", headers=headers)
    assert exec_res.status_code == 200

    # 4. Listar backups con filtro 'automatico'
    list_res = await client.get("/api/v1/backups?tipo=automatico", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    # Debe haber al menos un backup automático registrado
    assert any(b["tipo"] == "automatico" for b in items)


@pytest.mark.asyncio
async def test_cu37_estadisticas_y_visibilidad_nube_local(client: AsyncClient):
    login_res = await login(client, "admin@demo.test", "Admin123!", empresa_slug="demo")
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    stats_res = await client.get("/api/v1/backups/estadisticas", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_backups"] >= 1
    assert stats["total_locales"] >= 1
    assert stats["total_nube"] >= 1
    assert "AWS S3" in stats["proveedor_nube"]
    assert stats["espacio_local_legible"] is not None
    assert stats["espacio_nube_legible"] is not None


@pytest.mark.asyncio
async def test_cu37_cliente_no_autorizado_para_backups(client: AsyncClient):
    # Un cliente regular no puede acceder a las funciones de backup
    login_res = await login(client, "cliente@demo.test", "Cliente123!", empresa_slug="demo")
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/backups", headers=headers)
    assert res.status_code == 403

