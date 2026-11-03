from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.conftest import login

DEMO_ADMIN = ("admin@demo.test", "Admin123!")


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    response = await login(client, DEMO_ADMIN[0], DEMO_ADMIN[1], empresa_slug="demo")
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# =========================================================================
# CU-15: ADMINISTRAR PROVEEDORES TEXTILES
# =========================================================================

@pytest.mark.asyncio
async def test_cu15_proveedores_crud_y_nit_duplicado(client: AsyncClient):
    headers = await _admin_headers(client)
    suffix = uuid4().hex[:6]
    nit = f"NIT-{suffix}"

    # 1. Crear proveedor exitoso
    create_payload = {
        "nombre": f"Proveedor Textil {suffix}",
        "nit": nit,
        "correo": f"proveedor{suffix}@textil.com",
        "telefono": "+59170011223",
    }
    res = await client.post("/api/v1/proveedores", json=create_payload, headers=headers)
    assert res.status_code == 201, res.text
    prov_data = res.json()
    assert prov_data["nombre"] == create_payload["nombre"]
    assert prov_data["nit"] == nit
    prov_id = prov_data["id"]

    try:
        # 2. Intento de NIT duplicado en la misma empresa (Regla CU-15 -> 409 Conflict)
        dup_res = await client.post("/api/v1/proveedores", json=create_payload, headers=headers)
        assert dup_res.status_code == 409, dup_res.text
        assert dup_res.json()["detail"]["code"] == "NIT_DUPLICADO"

        # 3. Listar proveedores
        list_res = await client.get("/api/v1/proveedores", params={"search": suffix}, headers=headers)
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 4. Modificar proveedor
        upd_res = await client.put(
            f"/api/v1/proveedores/{prov_id}",
            json={"nombre": f"Proveedor Modificado {suffix}"},
            headers=headers,
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["nombre"] == f"Proveedor Modificado {suffix}"

    finally:
        # 5. Baja logica
        del_res = await client.delete(f"/api/v1/proveedores/{prov_id}", headers=headers)
        assert del_res.status_code == 200


# =========================================================================
# CU-16: ADMINISTRAR TEMPORADAS Y COLECCIONES COMERCIALES
# =========================================================================

@pytest.mark.asyncio
async def test_cu16_temporadas_fechas_incongruentes(client: AsyncClient):
    headers = await _admin_headers(client)
    suffix = uuid4().hex[:6]

    # 1. Intento de rango de fechas incongruente (fecha_inicio >= fecha_fin -> 422)
    invalid_payload = {
        "nombre": f"Temporada Invalida {suffix}",
        "fecha_inicio": "2026-12-01",
        "fecha_fin": "2026-06-01",
    }
    err_res = await client.post("/api/v1/temporadas-colecciones/temporadas", json=invalid_payload, headers=headers)
    assert err_res.status_code == 422, err_res.text

    # 2. Crear temporada valida
    valid_payload = {
        "nombre": f"Otono-Invierno {suffix}",
        "fecha_inicio": "2026-03-01",
        "fecha_fin": "2026-08-31",
    }
    temp_res = await client.post("/api/v1/temporadas-colecciones/temporadas", json=valid_payload, headers=headers)
    assert temp_res.status_code == 201, temp_res.text
    temp_id = temp_res.json()["id"]

    # 3. Crear coleccion
    col_payload = {
        "nombre": f"Coleccion Denim {suffix}",
        "anio": 2026,
    }
    col_res = await client.post("/api/v1/temporadas-colecciones/colecciones", json=col_payload, headers=headers)
    assert col_res.status_code == 201, col_res.text
    col_id = col_res.json()["id"]

    try:
        # 4. Consultar resumen
        all_res = await client.get("/api/v1/temporadas-colecciones", headers=headers)
        assert all_res.status_code == 200
        data = all_res.json()
        assert any(t["id"] == temp_id for t in data["temporadas"])
        assert any(c["id"] == col_id for c in data["colecciones"])
    finally:
        await client.delete(f"/api/v1/temporadas-colecciones/temporadas/{temp_id}", headers=headers)
        await client.delete(f"/api/v1/temporadas-colecciones/colecciones/{col_id}", headers=headers)


# =========================================================================
# CU-11: ADMINISTRAR SUCURSALES (REGLA BR-02)
# =========================================================================

@pytest.mark.asyncio
async def test_cu11_sucursales_limite_plan_br02(client: AsyncClient):
    headers = await _admin_headers(client)

    # 1. Consultar sucursales existentes y limites de plan
    res = await client.get("/api/v1/sucursales", headers=headers)
    assert res.status_code == 200
    info = res.json()
    limite = info["limite_plan"]
    activas = info["activas"]
    assert limite >= 2

    suffix = uuid4().hex[:6]
    sucursal_payload = {
        "nombre": f"Sucursal Test {suffix}",
        "ciudad_id": 1,
        "direccion": "Av. San Martin #450",
        "telefono": "33445566",
        "es_matriz": False,
    }

    if activas < limite:
        # Debe permitir crear si hay cupo
        create_res = await client.post("/api/v1/sucursales", json=sucursal_payload, headers=headers)
        assert create_res.status_code == 201
        suc_id = create_res.json()["id"]
        # Limpiar
        await client.delete(f"/api/v1/sucursales/{suc_id}", headers=headers)
    else:
        # Si ya llego al limite, debe rechazar con HTTP 402 por regla BR-02
        block_res = await client.post("/api/v1/sucursales", json=sucursal_payload, headers=headers)
        assert block_res.status_code == 402, block_res.text
        assert block_res.json()["detail"]["code"] == "LIMITE_SUCURSALES_ALCANZADO"


# =========================================================================
# CU-10: USUARIOS Y ROLES POR EMPRESA (REGLA BR-12)
# =========================================================================

@pytest.mark.asyncio
async def test_cu10_empleados_roles_y_regla_br12(client: AsyncClient):
    headers = await _admin_headers(client)
    suffix = uuid4().hex[:6]

    # 1. Regla BR-12: Un Administrador de Empresa NO puede asignar el rol superadmin -> 403 Forbidden
    superadmin_payload = {
        "nombre": f"Hacker Intento {suffix}",
        "correo": f"hacker{suffix}@demo.com",
        "password": "Password123!",
        "rol": "superadmin",
    }
    block_res = await client.post("/api/v1/empleados", json=superadmin_payload, headers=headers)
    assert block_res.status_code == 403, block_res.text
    assert block_res.json()["detail"]["code"] == "ROL_NO_PERMITIDO"

    # 2. Alta valida de empleado cajero
    valid_payload = {
        "nombre": f"Cajero Empleado {suffix}",
        "correo": f"cajero{suffix}@demo.com",
        "password": "Password123!",
        "rol": "cajero",
    }
    create_res = await client.post("/api/v1/empleados", json=valid_payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    emp_data = create_res.json()
    assert emp_data["rol_nombre"] == "cajero"
    emp_id = emp_data["id"]

    try:
        # 3. Correo duplicado en el tenant -> 409 Conflict
        dup_res = await client.post("/api/v1/empleados", json=valid_payload, headers=headers)
        assert dup_res.status_code == 409
        assert dup_res.json()["detail"]["code"] == "CORREO_DUPLICADO"

        # 4. Modificar rol o datos
        upd_res = await client.put(
            f"/api/v1/empleados/{emp_id}",
            json={"telefono": "+59178899001"},
            headers=headers,
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["telefono"] == "+59178899001"
    finally:
        # 5. Baja logica y revocacion de sesiones
        del_res = await client.delete(f"/api/v1/empleados/{emp_id}", headers=headers)
        assert del_res.status_code == 200


# =========================================================================
# CU-12, CU-13, CU-14: CATALOGO, VARIANTES Y FILTROS
# =========================================================================

@pytest.mark.asyncio
async def test_cu12_catalogo_prendas_y_variantes_sku(client: AsyncClient):
    headers = await _admin_headers(client)
    suffix = uuid4().hex[:6]

    # Obtener auxiliares para ids validos
    aux_res = await client.get("/api/v1/catalogo/auxiliares?empresa_slug=demo")
    assert aux_res.status_code == 200
    aux = aux_res.json()
    cat_id = aux["categorias"][0]["id"]
    color_id = aux["colores"][0]["id"]
    talla_id = aux["tallas"][0]["id"]

    sku_code = f"SKU-{suffix}-01"

    # 1. Crear prenda con variante SKU
    prenda_payload = {
        "codigo": f"COD-{suffix}",
        "nombre": f"Camisa Denim Oxford {suffix}",
        "precio_base": 180.00,
        "categoria_id": cat_id,
        "genero": "unisex",
        "marca": "FashionStore",
        "variantes": [
            {
                "talla_id": talla_id,
                "color_id": color_id,
                "sku": sku_code,
                "precio_venta": 185.00,
                "costo": 90.00,
            }
        ],
    }
    res = await client.post("/api/v1/catalogo/admin/prendas", json=prenda_payload, headers=headers)
    assert res.status_code == 201, res.text
    prenda_data = res.json()
    prenda_id = prenda_data["id"]
    assert len(prenda_data["variantes"]) == 1

    try:
        # 2. SKU duplicado en tenant -> 409 Conflict
        dup_sku_payload = {
            "codigo": f"COD2-{suffix}",
            "nombre": f"Otra Camisa {suffix}",
            "precio_base": 190.00,
            "categoria_id": cat_id,
            "variantes": [
                {
                    "talla_id": talla_id,
                    "color_id": color_id,
                    "sku": sku_code,  # Duplicado
                    "precio_venta": 190.00,
                }
            ],
        }
        dup_res = await client.post("/api/v1/catalogo/admin/prendas", json=dup_sku_payload, headers=headers)
        assert dup_res.status_code == 409
        assert dup_res.json()["detail"]["code"] == "SKU_DUPLICADO"

        # 3. CU-13: Consulta publica de catalogo
        pub_res = await client.get("/api/v1/catalogo/prendas?empresa_slug=demo")
        assert pub_res.status_code == 200
        pub_data = pub_res.json()
        assert pub_data["version_catalogo"] >= 1
        assert any(p["id"] == prenda_id for p in pub_data["items"])

        # 4. CU-14: Filtrado multidimensional
        filtro_res = await client.get(
            f"/api/v1/catalogo/prendas?empresa_slug=demo&search={suffix}&precio_min=100&precio_max=300"
        )
        assert filtro_res.status_code == 200
        filtro_data = filtro_res.json()
        assert len(filtro_data["items"]) == 1
        assert filtro_data["items"][0]["id"] == prenda_id

        # 5. CU-14 Flujo alternativo: filtro sin coincidencias
        vacio_res = await client.get(
            f"/api/v1/catalogo/prendas?empresa_slug=demo&search=inmposible_que_exista_{suffix}"
        )
        assert vacio_res.status_code == 200
        assert vacio_res.json()["total"] == 0
        assert len(vacio_res.json()["items"]) == 0

    finally:
        await client.delete(f"/api/v1/catalogo/admin/prendas/{prenda_id}", headers=headers)
