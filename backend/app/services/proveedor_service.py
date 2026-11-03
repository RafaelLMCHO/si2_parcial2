import logging
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection
from app.schemas.proveedor import (
    ProveedorCreateRequest,
    ProveedorListResponse,
    ProveedorOut,
    ProveedorUpdateRequest,
)

logger = logging.getLogger(__name__)


async def list_proveedores(
    empresa_id: str,
    user_id: str,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ProveedorListResponse:
    async with tenant_connection(empresa_id, user_id) as conn:
        conditions = ["empresa_id = $1", "deleted_at IS NULL"]
        params: list[object] = [empresa_id]

        if search:
            params.append(f"%{search.strip().lower()}%")
            conditions.append(f"(lower(nombre) LIKE ${len(params)} OR lower(nit) LIKE ${len(params)})")

        where_clause = " AND ".join(conditions)

        count_sql = f"SELECT count(*)::integer FROM proveedor WHERE {where_clause}"
        total = await conn.fetchval(count_sql, *params)

        params.extend([limit, offset])
        query_sql = f"""
            SELECT id,
                   empresa_id,
                   nombre,
                   nit,
                   correo,
                   telefono,
                   created_at,
                   updated_at
              FROM proveedor
             WHERE {where_clause}
             ORDER BY nombre ASC
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """
        rows = await conn.fetch(query_sql, *params)

        items = [
            ProveedorOut(
                id=r["id"],
                empresa_id=r["empresa_id"],
                nombre=r["nombre"],
                nit=r["nit"],
                correo=r["correo"],
                telefono=r["telefono"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]
        return ProveedorListResponse(total=total, items=items)


async def get_proveedor(empresa_id: str, user_id: str, proveedor_id: str) -> ProveedorOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT id,
                   empresa_id,
                   nombre,
                   nit,
                   correo,
                   telefono,
                   created_at,
                   updated_at
              FROM proveedor
             WHERE id = $1
               AND empresa_id = $2
               AND deleted_at IS NULL
            """,
            UUID(proveedor_id),
            UUID(empresa_id),
        )
        if row is None:
            raise api_error(404, "PROVEEDOR_NO_ENCONTRADO", "El proveedor no existe en su empresa")

        return ProveedorOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            nit=row["nit"],
            correo=row["correo"],
            telefono=row["telefono"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def create_proveedor(
    empresa_id: str,
    user_id: str,
    data: ProveedorCreateRequest,
) -> ProveedorOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        # Validar unicidad de NIT en el tenant (regla CU-15)
        existing = await conn.fetchval(
            """
            SELECT id
              FROM proveedor
             WHERE empresa_id = $1
               AND nit = $2
               AND deleted_at IS NULL
            """,
            UUID(empresa_id),
            data.nit.strip(),
        )
        if existing is not None:
            raise api_error(
                409,
                "NIT_DUPLICADO",
                f"Ya existe un proveedor registrado con el NIT '{data.nit}' en esta empresa",
            )

        row = await conn.fetchrow(
            """
            INSERT INTO proveedor (empresa_id, nombre, nit, correo, telefono)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, empresa_id, nombre, nit, correo, telefono, created_at, updated_at
            """,
            UUID(empresa_id),
            data.nombre.strip(),
            data.nit.strip(),
            data.correo.strip() if data.correo else None,
            data.telefono.strip() if data.telefono else None,
        )

        proveedor = ProveedorOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            nit=row["nit"],
            correo=row["correo"],
            telefono=row["telefono"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # Auditoria BR-13
    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="proveedor",
        entidad_id=proveedor.id,
        datos_despues=data.model_dump(mode="json"),
    )
    return proveedor


async def update_proveedor(
    empresa_id: str,
    user_id: str,
    proveedor_id: str,
    data: ProveedorUpdateRequest,
) -> ProveedorOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        current = await conn.fetchrow(
            """
            SELECT id, nombre, nit, correo, telefono
              FROM proveedor
             WHERE id = $1
               AND empresa_id = $2
               AND deleted_at IS NULL
            """,
            UUID(proveedor_id),
            UUID(empresa_id),
        )
        if current is None:
            raise api_error(404, "PROVEEDOR_NO_ENCONTRADO", "El proveedor no existe")

        new_nit = data.nit.strip() if data.nit is not None else current["nit"]
        if new_nit != current["nit"]:
            conflict = await conn.fetchval(
                """
                SELECT id
                  FROM proveedor
                 WHERE empresa_id = $1
                   AND nit = $2
                   AND id <> $3
                   AND deleted_at IS NULL
                """,
                UUID(empresa_id),
                new_nit,
                UUID(proveedor_id),
            )
            if conflict is not None:
                raise api_error(409, "NIT_DUPLICADO", f"El NIT '{new_nit}' ya pertenece a otro proveedor")

        new_nombre = data.nombre.strip() if data.nombre is not None else current["nombre"]
        new_correo = data.correo.strip() if data.correo is not None else current["correo"]
        new_telefono = data.telefono.strip() if data.telefono is not None else current["telefono"]

        row = await conn.fetchrow(
            """
            UPDATE proveedor
               SET nombre = $1,
                   nit = $2,
                   correo = $3,
                   telefono = $4,
                   updated_at = now()
             WHERE id = $5
               AND empresa_id = $6
            RETURNING id, empresa_id, nombre, nit, correo, telefono, created_at, updated_at
            """,
            new_nombre,
            new_nit,
            new_correo,
            new_telefono,
            UUID(proveedor_id),
            UUID(empresa_id),
        )

        proveedor = ProveedorOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            nit=row["nit"],
            correo=row["correo"],
            telefono=row["telefono"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="proveedor",
        entidad_id=proveedor.id,
        datos_antes={
            "nombre": current["nombre"],
            "nit": current["nit"],
            "correo": current["correo"],
            "telefono": current["telefono"],
        },
        datos_despues=data.model_dump(exclude_unset=True, mode="json"),
    )
    return proveedor


async def delete_proveedor(
    empresa_id: str,
    user_id: str,
    proveedor_id: str,
) -> dict[str, str]:
    async with tenant_connection(empresa_id, user_id) as conn:
        result = await conn.execute(
            """
            UPDATE proveedor
               SET deleted_at = now(),
                   updated_at = now()
             WHERE id = $1
               AND empresa_id = $2
               AND deleted_at IS NULL
            """,
            UUID(proveedor_id),
            UUID(empresa_id),
        )
        if result == "UPDATE 0":
            raise api_error(404, "PROVEEDOR_NO_ENCONTRADO", "El proveedor no existe o ya fue eliminado")

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="delete",
        entidad="proveedor",
        entidad_id=proveedor_id,
    )
    return {"mensaje": "Proveedor eliminado correctamente"}
