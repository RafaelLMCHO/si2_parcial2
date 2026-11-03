import logging
from decimal import Decimal
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection
from app.schemas.catalogo import (
    AuxiliaresCatalogoResponse,
    ItemSimple,
    PrendaCreateRequest,
    PrendaListResponse,
    PrendaOut,
    PrendaUpdateRequest,
    VarianteCreateRequest,
    VarianteOut,
    VarianteUpdateRequest,
)

logger = logging.getLogger(__name__)


async def _increment_catalog_version(conn, empresa_id: UUID) -> int:
    version = await conn.fetchval(
        """
        INSERT INTO catalogo_version (empresa_id, version, actualizado_en)
        VALUES ($1, 1, now())
        ON CONFLICT (empresa_id)
        DO UPDATE SET version = catalogo_version.version + 1,
                      actualizado_en = now()
        RETURNING version
        """,
        empresa_id,
    )
    return int(version)


async def get_catalog_version(conn, empresa_id: UUID) -> int:
    v = await conn.fetchval("SELECT version FROM catalogo_version WHERE empresa_id = $1", empresa_id)
    return int(v) if v is not None else 1


async def list_prendas(
    empresa_id: str,
    user_id: str | None = None,
    categoria_id: str | None = None,
    temporada_id: str | None = None,
    coleccion_id: str | None = None,
    talla_id: int | None = None,
    color_id: int | None = None,
    precio_min: Decimal | None = None,
    precio_max: Decimal | None = None,
    genero: str | None = None,
    search: str | None = None,
    solo_activas: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> PrendaListResponse:
    async with tenant_connection(empresa_id, user_id) as conn:
        version = await get_catalog_version(conn, UUID(empresa_id))

        conditions = ["p.empresa_id = $1", "p.deleted_at IS NULL"]
        params: list[object] = [UUID(empresa_id)]

        if solo_activas:
            conditions.append("p.estado = 'activa'")

        if categoria_id:
            params.append(UUID(categoria_id))
            conditions.append(f"p.categoria_id = ${len(params)}")

        if temporada_id:
            params.append(UUID(temporada_id))
            conditions.append(f"p.temporada_id = ${len(params)}")

        if coleccion_id:
            params.append(UUID(coleccion_id))
            conditions.append(f"p.coleccion_id = ${len(params)}")

        if genero:
            params.append(genero.lower())
            conditions.append(f"p.genero = ${len(params)}")

        if precio_min is not None:
            params.append(precio_min)
            conditions.append(f"p.precio_base >= ${len(params)}")

        if precio_max is not None:
            params.append(precio_max)
            conditions.append(f"p.precio_base <= ${len(params)}")

        if search:
            params.append(f"%{search.strip().lower()}%")
            conditions.append(f"(lower(p.nombre) LIKE ${len(params)} OR lower(p.codigo) LIKE ${len(params)} OR lower(COALESCE(p.marca, '')) LIKE ${len(params)})")

        # Filtros a nivel de variantes (CU-14: talla, color)
        if talla_id is not None or color_id is not None:
            variant_conds = ["v_filter.prenda_id = p.id", "v_filter.deleted_at IS NULL"]
            if talla_id is not None:
                params.append(talla_id)
                variant_conds.append(f"v_filter.talla_id = ${len(params)}")
            if color_id is not None:
                params.append(color_id)
                variant_conds.append(f"v_filter.color_id = ${len(params)}")
            conditions.append(f"EXISTS (SELECT 1 FROM variante v_filter WHERE {' AND '.join(variant_conds)})")

        where_clause = " AND ".join(conditions)

        count_sql = f"SELECT count(*)::integer FROM prenda p WHERE {where_clause}"
        total = await conn.fetchval(count_sql, *params)

        params.extend([limit, offset])
        prendas_sql = f"""
            SELECT p.id,
                   p.empresa_id,
                   p.codigo,
                   p.nombre,
                   p.descripcion,
                   p.marca,
                   p.genero,
                   p.precio_base,
                   p.moneda,
                   p.categoria_id,
                   c.nombre AS categoria_nombre,
                   p.temporada_id,
                   t.nombre AS temporada_nombre,
                   p.coleccion_id,
                   col.nombre AS coleccion_nombre,
                   p.proveedor_id,
                   pr.nombre AS proveedor_nombre,
                   p.imagen_url,
                   p.estado,
                   p.created_at,
                   p.updated_at
              FROM prenda p
              JOIN categoria c ON c.id = p.categoria_id
              LEFT JOIN temporada t ON t.id = p.temporada_id
              LEFT JOIN coleccion col ON col.id = p.coleccion_id
              LEFT JOIN proveedor pr ON pr.id = p.proveedor_id
             WHERE {where_clause}
             ORDER BY p.created_at DESC
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """
        rows = await conn.fetch(prendas_sql, *params)
        if not rows:
            return PrendaListResponse(total=total, version_catalogo=version, items=[])

        prenda_ids = [r["id"] for r in rows]

        # Cargar variantes de todas las prendas consultadas
        variantes_rows = await conn.fetch(
            """
            SELECT v.id,
                   v.prenda_id,
                   v.talla_id,
                   ta.nombre AS talla_nombre,
                   v.color_id,
                   co.nombre AS color_nombre,
                   co.hex AS color_hex,
                   v.sku,
                   v.codigo_barras,
                   v.precio_venta,
                   v.costo,
                   v.estado,
                   v.created_at,
                   v.updated_at
              FROM variante v
              JOIN talla ta ON ta.id = v.talla_id
              JOIN color co ON co.id = v.color_id
             WHERE v.prenda_id = ANY($1::uuid[])
               AND v.deleted_at IS NULL
             ORDER BY ta.orden ASC, co.nombre ASC
            """,
            prenda_ids,
        )

        variantes_by_prenda: dict[UUID, list[VarianteOut]] = {pid: [] for pid in prenda_ids}
        for vr in variantes_rows:
            variantes_by_prenda[vr["prenda_id"]].append(
                VarianteOut(
                    id=vr["id"],
                    prenda_id=vr["prenda_id"],
                    talla_id=vr["talla_id"],
                    talla_nombre=vr["talla_nombre"],
                    color_id=vr["color_id"],
                    color_nombre=vr["color_nombre"],
                    color_hex=vr["color_hex"],
                    sku=vr["sku"],
                    codigo_barras=vr["codigo_barras"],
                    precio_venta=vr["precio_venta"],
                    costo=vr["costo"],
                    estado=vr["estado"],
                    created_at=vr["created_at"],
                    updated_at=vr["updated_at"],
                )
            )

        items = [
            PrendaOut(
                id=r["id"],
                empresa_id=r["empresa_id"],
                codigo=r["codigo"],
                nombre=r["nombre"],
                descripcion=r["descripcion"],
                marca=r["marca"],
                genero=r["genero"],
                precio_base=r["precio_base"],
                moneda=r["moneda"],
                categoria_id=r["categoria_id"],
                categoria_nombre=r["categoria_nombre"],
                temporada_id=r["temporada_id"],
                temporada_nombre=r["temporada_nombre"],
                coleccion_id=r["coleccion_id"],
                coleccion_nombre=r["coleccion_nombre"],
                proveedor_id=r["proveedor_id"],
                proveedor_nombre=r["proveedor_nombre"],
                imagen_url=r["imagen_url"],
                estado=r["estado"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                variantes=variantes_by_prenda.get(r["id"], []),
            )
            for r in rows
        ]

        return PrendaListResponse(total=total, version_catalogo=version, items=items)


async def get_prenda(empresa_id: str, prenda_id: str, user_id: str | None = None) -> PrendaOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        r = await conn.fetchrow(
            """
            SELECT p.id,
                   p.empresa_id,
                   p.codigo,
                   p.nombre,
                   p.descripcion,
                   p.marca,
                   p.genero,
                   p.precio_base,
                   p.moneda,
                   p.categoria_id,
                   c.nombre AS categoria_nombre,
                   p.temporada_id,
                   t.nombre AS temporada_nombre,
                   p.coleccion_id,
                   col.nombre AS coleccion_nombre,
                   p.proveedor_id,
                   pr.nombre AS proveedor_nombre,
                   p.imagen_url,
                   p.estado,
                   p.created_at,
                   p.updated_at
              FROM prenda p
              JOIN categoria c ON c.id = p.categoria_id
              LEFT JOIN temporada t ON t.id = p.temporada_id
              LEFT JOIN coleccion col ON col.id = p.coleccion_id
              LEFT JOIN proveedor pr ON pr.id = p.proveedor_id
             WHERE p.id = $1
               AND p.empresa_id = $2
               AND p.deleted_at IS NULL
            """,
            UUID(prenda_id),
            UUID(empresa_id),
        )
        if r is None:
            raise api_error(404, "PRENDA_NO_ENCONTRADA", "La prenda no existe en el catalogo")

        variantes_rows = await conn.fetch(
            """
            SELECT v.id,
                   v.prenda_id,
                   v.talla_id,
                   ta.nombre AS talla_nombre,
                   v.color_id,
                   co.nombre AS color_nombre,
                   co.hex AS color_hex,
                   v.sku,
                   v.codigo_barras,
                   v.precio_venta,
                   v.costo,
                   v.estado,
                   v.created_at,
                   v.updated_at
              FROM variante v
              JOIN talla ta ON ta.id = v.talla_id
              JOIN color co ON co.id = v.color_id
             WHERE v.prenda_id = $1
               AND v.deleted_at IS NULL
             ORDER BY ta.orden ASC, co.nombre ASC
            """,
            UUID(prenda_id),
        )

        variantes = [
            VarianteOut(
                id=vr["id"],
                prenda_id=vr["prenda_id"],
                talla_id=vr["talla_id"],
                talla_nombre=vr["talla_nombre"],
                color_id=vr["color_id"],
                color_nombre=vr["color_nombre"],
                color_hex=vr["color_hex"],
                sku=vr["sku"],
                codigo_barras=vr["codigo_barras"],
                precio_venta=vr["precio_venta"],
                costo=vr["costo"],
                estado=vr["estado"],
                created_at=vr["created_at"],
                updated_at=vr["updated_at"],
            )
            for vr in variantes_rows
        ]

        return PrendaOut(
            id=r["id"],
            empresa_id=r["empresa_id"],
            codigo=r["codigo"],
            nombre=r["nombre"],
            descripcion=r["descripcion"],
            marca=r["marca"],
            genero=r["genero"],
            precio_base=r["precio_base"],
            moneda=r["moneda"],
            categoria_id=r["categoria_id"],
            categoria_nombre=r["categoria_nombre"],
            temporada_id=r["temporada_id"],
            temporada_nombre=r["temporada_nombre"],
            coleccion_id=r["coleccion_id"],
            coleccion_nombre=r["coleccion_nombre"],
            proveedor_id=r["proveedor_id"],
            proveedor_nombre=r["proveedor_nombre"],
            imagen_url=r["imagen_url"],
            estado=r["estado"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            variantes=variantes,
        )


async def create_prenda(
    empresa_id: str,
    user_id: str,
    data: PrendaCreateRequest,
) -> PrendaOut:
    if data.precio_base < 0:
        raise api_error(422, "PRECIO_INVALIDO", "El precio base no puede ser negativo")

    async with tenant_connection(empresa_id, user_id) as conn:
        # Validar codigo de prenda unico en tenant
        dup_cod = await conn.fetchval(
            "SELECT id FROM prenda WHERE empresa_id = $1 AND lower(codigo) = lower($2) AND deleted_at IS NULL",
            UUID(empresa_id),
            data.codigo.strip(),
        )
        if dup_cod is not None:
            raise api_error(409, "CODIGO_PRENDA_DUPLICADO", f"El codigo de estilo '{data.codigo}' ya esta en uso")

        # Validar categoria en tenant
        cat_nombre = await conn.fetchval(
            "SELECT nombre FROM categoria WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            data.categoria_id,
            UUID(empresa_id),
        )
        if cat_nombre is None:
            raise api_error(404, "CATEGORIA_NO_ENCONTRADA", "La categoria seleccionada no existe")

        # Validar SKUs unicos antes de insertar
        skus_vistos = set()
        for v in data.variantes:
            sku_clean = v.sku.strip()
            if sku_clean in skus_vistos:
                raise api_error(409, "SKU_DUPLICADO", f"El SKU '{sku_clean}' esta repetido en la solicitud")
            skus_vistos.add(sku_clean)

            dup_sku = await conn.fetchval(
                "SELECT id FROM variante WHERE empresa_id = $1 AND sku = $2 AND deleted_at IS NULL",
                UUID(empresa_id),
                sku_clean,
            )
            if dup_sku is not None:
                raise api_error(
                    409,
                    "SKU_DUPLICADO",
                    f"El codigo SKU '{sku_clean}' ya existe en el catalogo de su empresa",
                )

        # Crear prenda
        row = await conn.fetchrow(
            """
            INSERT INTO prenda (
                empresa_id, categoria_id, temporada_id, coleccion_id, proveedor_id,
                codigo, nombre, descripcion, marca, genero, precio_base, moneda, imagen_url, estado
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'BOB', $12, 'activa')
            RETURNING id, empresa_id, codigo, nombre, descripcion, marca, genero,
                      precio_base, moneda, categoria_id, temporada_id, coleccion_id,
                      proveedor_id, imagen_url, estado, created_at, updated_at
            """,
            UUID(empresa_id),
            data.categoria_id,
            data.temporada_id,
            data.coleccion_id,
            data.proveedor_id,
            data.codigo.strip(),
            data.nombre.strip(),
            data.descripcion.strip() if data.descripcion else None,
            data.marca.strip() if data.marca else None,
            data.genero,
            data.precio_base,
            data.imagen_url.strip() if data.imagen_url else None,
        )
        prenda_id = row["id"]

        # Insertar variantes
        variantes_creadas: list[VarianteOut] = []
        for v in data.variantes:
            v_row = await conn.fetchrow(
                """
                INSERT INTO variante (
                    empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, costo, estado
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'activa')
                RETURNING id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, costo, estado, created_at, updated_at
                """,
                UUID(empresa_id),
                prenda_id,
                v.color_id,
                v.talla_id,
                v.sku.strip(),
                v.codigo_barras.strip() if v.codigo_barras else None,
                v.precio_venta,
                v.costo,
            )

            # Historial de precio
            await conn.execute(
                """
                INSERT INTO precio_historial (empresa_id, variante_id, precio_anterior, precio_nuevo, motivo, creado_por)
                VALUES ($1, $2, $3, $4, 'Precio inicial de creacion', $5)
                """,
                UUID(empresa_id),
                v_row["id"],
                v.precio_venta,
                v.precio_venta,
                UUID(user_id),
            )

            ta_nombre = await conn.fetchval("SELECT nombre FROM talla WHERE id = $1", v.talla_id)
            co_info = await conn.fetchrow("SELECT nombre, hex FROM color WHERE id = $1", v.color_id)

            variantes_creadas.append(
                VarianteOut(
                    id=v_row["id"],
                    prenda_id=prenda_id,
                    talla_id=v.talla_id,
                    talla_nombre=ta_nombre,
                    color_id=v.color_id,
                    color_nombre=co_info["nombre"] if co_info else None,
                    color_hex=co_info["hex"] if co_info else None,
                    sku=v_row["sku"],
                    codigo_barras=v_row["codigo_barras"],
                    precio_venta=v_row["precio_venta"],
                    costo=v_row["costo"],
                    estado=v_row["estado"],
                    created_at=v_row["created_at"],
                    updated_at=v_row["updated_at"],
                )
            )

        await _increment_catalog_version(conn, UUID(empresa_id))

        prenda = PrendaOut(
            id=prenda_id,
            empresa_id=row["empresa_id"],
            codigo=row["codigo"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            marca=row["marca"],
            genero=row["genero"],
            precio_base=row["precio_base"],
            moneda=row["moneda"],
            categoria_id=row["categoria_id"],
            categoria_nombre=cat_nombre,
            temporada_id=row["temporada_id"],
            coleccion_id=row["coleccion_id"],
            proveedor_id=row["proveedor_id"],
            imagen_url=row["imagen_url"],
            estado=row["estado"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            variantes=variantes_creadas,
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="prenda",
        entidad_id=prenda.id,
        datos_despues={
            "codigo": prenda.codigo,
            "nombre": prenda.nombre,
            "variantes_count": len(variantes_creadas),
        },
    )
    return prenda


async def update_prenda(
    empresa_id: str,
    user_id: str,
    prenda_id: str,
    data: PrendaUpdateRequest,
) -> PrendaOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        current = await conn.fetchrow(
            "SELECT id, codigo, nombre, estado FROM prenda WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            UUID(prenda_id),
            UUID(empresa_id),
        )
        if current is None:
            raise api_error(404, "PRENDA_NO_ENCONTRADA", "La prenda no existe")

        new_codigo = data.codigo.strip() if data.codigo is not None else current["codigo"]
        if new_codigo.lower() != current["codigo"].lower():
            dup = await conn.fetchval(
                "SELECT id FROM prenda WHERE empresa_id = $1 AND lower(codigo) = lower($2) AND id <> $3 AND deleted_at IS NULL",
                UUID(empresa_id),
                new_codigo,
                UUID(prenda_id),
            )
            if dup is not None:
                raise api_error(409, "CODIGO_PRENDA_DUPLICADO", f"El codigo '{new_codigo}' ya pertenece a otra prenda")

        await conn.execute(
            """
            UPDATE prenda
               SET codigo = COALESCE($1, codigo),
                   nombre = COALESCE($2, nombre),
                   descripcion = COALESCE($3, descripcion),
                   marca = COALESCE($4, marca),
                   genero = COALESCE($5, genero),
                   precio_base = COALESCE($6, precio_base),
                   categoria_id = COALESCE($7, categoria_id),
                   temporada_id = COALESCE($8, temporada_id),
                   coleccion_id = COALESCE($9, coleccion_id),
                   proveedor_id = COALESCE($10, proveedor_id),
                   imagen_url = COALESCE($11, imagen_url),
                   estado = COALESCE($12, estado),
                   updated_at = now()
             WHERE id = $13 AND empresa_id = $14
            """,
            new_codigo,
            data.nombre.strip() if data.nombre else None,
            data.descripcion.strip() if data.descripcion else None,
            data.marca.strip() if data.marca else None,
            data.genero,
            data.precio_base,
            data.categoria_id,
            data.temporada_id,
            data.coleccion_id,
            data.proveedor_id,
            data.imagen_url.strip() if data.imagen_url else None,
            data.estado,
            UUID(prenda_id),
            UUID(empresa_id),
        )

        await _increment_catalog_version(conn, UUID(empresa_id))

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="prenda",
        entidad_id=prenda_id,
        datos_despues=data.model_dump(exclude_unset=True, mode="json"),
    )
    return await get_prenda(empresa_id, prenda_id, user_id)


async def delete_prenda(
    empresa_id: str,
    user_id: str,
    prenda_id: str,
) -> dict[str, str]:
    async with tenant_connection(empresa_id, user_id) as conn:
        result = await conn.execute(
            """
            UPDATE prenda
               SET deleted_at = now(),
                   estado = 'inactiva',
                   updated_at = now()
             WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL
            """,
            UUID(prenda_id),
            UUID(empresa_id),
        )
        if result == "UPDATE 0":
            raise api_error(404, "PRENDA_NO_ENCONTRADA", "La prenda no existe o ya fue dada de baja")

        # Baja logica de sus variantes
        await conn.execute(
            "UPDATE variante SET deleted_at = now(), estado = 'inactiva', updated_at = now() WHERE prenda_id = $1",
            UUID(prenda_id),
        )
        await _increment_catalog_version(conn, UUID(empresa_id))

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="delete",
        entidad="prenda",
        entidad_id=prenda_id,
    )
    return {"mensaje": "Prenda y variantes dadas de baja correctamente"}


# -------------------------------------------------------------------------
# VARIANTES (CU-12)
# -------------------------------------------------------------------------

async def add_variante_to_prenda(
    empresa_id: str,
    user_id: str,
    prenda_id: str,
    data: VarianteCreateRequest,
) -> VarianteOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        # Validar existencia de prenda
        prenda_ok = await conn.fetchval(
            "SELECT id FROM prenda WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
            UUID(prenda_id),
            UUID(empresa_id),
        )
        if prenda_ok is None:
            raise api_error(404, "PRENDA_NO_ENCONTRADA", "La prenda no existe")

        sku_clean = data.sku.strip()
        dup_sku = await conn.fetchval(
            "SELECT id FROM variante WHERE empresa_id = $1 AND sku = $2 AND deleted_at IS NULL",
            UUID(empresa_id),
            sku_clean,
        )
        if dup_sku is not None:
            raise api_error(409, "SKU_DUPLICADO", f"El codigo SKU '{sku_clean}' ya existe")

        row = await conn.fetchrow(
            """
            INSERT INTO variante (
                empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, costo, estado
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'activa')
            RETURNING id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, costo, estado, created_at, updated_at
            """,
            UUID(empresa_id),
            UUID(prenda_id),
            data.color_id,
            data.talla_id,
            sku_clean,
            data.codigo_barras.strip() if data.codigo_barras else None,
            data.precio_venta,
            data.costo,
        )

        await conn.execute(
            """
            INSERT INTO precio_historial (empresa_id, variante_id, precio_anterior, precio_nuevo, motivo, creado_por)
            VALUES ($1, $2, $3, $4, 'Alta de variante SKU', $5)
            """,
            UUID(empresa_id),
            row["id"],
            data.precio_venta,
            data.precio_venta,
            UUID(user_id),
        )

        ta_nombre = await conn.fetchval("SELECT nombre FROM talla WHERE id = $1", data.talla_id)
        co_info = await conn.fetchrow("SELECT nombre, hex FROM color WHERE id = $1", data.color_id)
        await _increment_catalog_version(conn, UUID(empresa_id))

        variante = VarianteOut(
            id=row["id"],
            prenda_id=UUID(prenda_id),
            talla_id=data.talla_id,
            talla_nombre=ta_nombre,
            color_id=data.color_id,
            color_nombre=co_info["nombre"] if co_info else None,
            color_hex=co_info["hex"] if co_info else None,
            sku=row["sku"],
            codigo_barras=row["codigo_barras"],
            precio_venta=row["precio_venta"],
            costo=row["costo"],
            estado=row["estado"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="variante",
        entidad_id=variante.id,
        datos_despues=data.model_dump(mode="json"),
    )
    return variante


async def get_auxiliares_catalogo(empresa_id: str, user_id: str | None = None) -> AuxiliaresCatalogoResponse:
    async with tenant_connection(empresa_id, user_id) as conn:
        cats = await conn.fetch(
            "SELECT id, nombre FROM categoria WHERE empresa_id = $1 AND deleted_at IS NULL ORDER BY nombre",
            UUID(empresa_id),
        )
        colores = await conn.fetch("SELECT id, nombre, hex FROM color ORDER BY nombre")
        tallas = await conn.fetch("SELECT id, nombre, orden FROM talla ORDER BY orden")
        temporadas = await conn.fetch(
            "SELECT id, nombre FROM temporada WHERE empresa_id = $1 ORDER BY fecha_inicio DESC NULLS LAST",
            UUID(empresa_id),
        )
        colecciones = await conn.fetch(
            "SELECT id, nombre, anio FROM coleccion WHERE empresa_id = $1 ORDER BY anio DESC NULLS LAST",
            UUID(empresa_id),
        )

        return AuxiliaresCatalogoResponse(
            categorias=[ItemSimple(id=str(c["id"]), nombre=c["nombre"]) for c in cats],
            colores=[ItemSimple(id=c["id"], nombre=c["nombre"], extra=c["hex"]) for c in colores],
            tallas=[ItemSimple(id=t["id"], nombre=t["nombre"]) for t in tallas],
            temporadas=[ItemSimple(id=str(te["id"]), nombre=te["nombre"]) for te in temporadas],
            colecciones=[ItemSimple(id=str(co["id"]), nombre=co["nombre"], extra=str(co["anio"]) if co["anio"] else None) for co in colecciones],
        )
