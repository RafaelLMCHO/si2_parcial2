import logging
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection
from app.schemas.sucursal import (
    SucursalCreateRequest,
    SucursalOut,
    SucursalesListResponse,
    SucursalUpdateRequest,
)

logger = logging.getLogger(__name__)


async def get_limite_sucursales(conn, empresa_id: UUID) -> tuple[int, str]:
    """Obtiene el limite de sucursales segun el plan activo (Regla BR-02)."""
    row = await conn.fetchrow(
        """
        SELECT COALESCE(pl.limite, 2) AS limite,
               p.codigo AS plan_codigo
          FROM suscripcion s
          JOIN plan p ON p.id = s.plan_id
          LEFT JOIN plan_limite pl ON pl.plan_id = p.id AND pl.recurso = 'sucursales'
         WHERE s.empresa_id = $1
           AND s.estado IN ('prueba', 'activa')
         ORDER BY s.fecha_inicio DESC, s.created_at DESC
         LIMIT 1
        """,
        empresa_id,
    )
    if row is None:
        # Por defecto plan basico = 2
        return 2, "basico"
    return int(row["limite"]), str(row["plan_codigo"])


async def list_sucursales(empresa_id: str, user_id: str) -> SucursalesListResponse:
    async with tenant_connection(empresa_id, user_id) as conn:
        limite, _ = await get_limite_sucursales(conn, UUID(empresa_id))

        rows = await conn.fetch(
            """
            SELECT s.id,
                   s.empresa_id,
                   s.ciudad_id,
                   c.nombre AS ciudad_nombre,
                   s.nombre,
                   s.direccion,
                   s.telefono,
                   s.es_matriz,
                   s.estado,
                   s.created_at,
                   s.updated_at
              FROM sucursal s
              JOIN ciudad c ON c.id = s.ciudad_id
             WHERE s.empresa_id = $1
               AND s.deleted_at IS NULL
             ORDER BY s.es_matriz DESC, s.nombre ASC
            """,
            UUID(empresa_id),
        )

        items = [
            SucursalOut(
                id=r["id"],
                empresa_id=r["empresa_id"],
                ciudad_id=r["ciudad_id"],
                ciudad_nombre=r["ciudad_nombre"],
                nombre=r["nombre"],
                direccion=r["direccion"],
                telefono=r["telefono"],
                es_matriz=r["es_matriz"],
                estado=r["estado"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

        activas = sum(1 for it in items if it.estado == "activa")
        return SucursalesListResponse(
            total=len(items),
            activas=activas,
            limite_plan=limite,
            items=items,
        )


async def get_sucursal(empresa_id: str, user_id: str, sucursal_id: str) -> SucursalOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT s.id,
                   s.empresa_id,
                   s.ciudad_id,
                   c.nombre AS ciudad_nombre,
                   s.nombre,
                   s.direccion,
                   s.telefono,
                   s.es_matriz,
                   s.estado,
                   s.created_at,
                   s.updated_at
              FROM sucursal s
              JOIN ciudad c ON c.id = s.ciudad_id
             WHERE s.id = $1
               AND s.empresa_id = $2
               AND s.deleted_at IS NULL
            """,
            UUID(sucursal_id),
            UUID(empresa_id),
        )
        if row is None:
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal no existe")

        return SucursalOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            ciudad_id=row["ciudad_id"],
            ciudad_nombre=row["ciudad_nombre"],
            nombre=row["nombre"],
            direccion=row["direccion"],
            telefono=row["telefono"],
            es_matriz=row["es_matriz"],
            estado=row["estado"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def create_sucursal(
    empresa_id: str,
    user_id: str,
    data: SucursalCreateRequest,
) -> SucursalOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        limite, plan_codigo = await get_limite_sucursales(conn, UUID(empresa_id))

        activas_actuales = await conn.fetchval(
            """
            SELECT count(*)::integer
              FROM sucursal
             WHERE empresa_id = $1
               AND estado = 'activa'
               AND deleted_at IS NULL
            """,
            UUID(empresa_id),
        )

        # Regla BR-02: Rechazar con HTTP 402 si excede el limite del plan
        if activas_actuales >= limite:
            raise api_error(
                402,
                "LIMITE_SUCURSALES_ALCANZADO",
                f"Limite de sucursales alcanzado ({limite}) para su plan de suscripcion. "
                "Debe actualizar su plan para habilitar nuevas sucursales.",
            )

        # Validar ciudad existente
        ciudad_nombre = await conn.fetchval("SELECT nombre FROM ciudad WHERE id = $1", data.ciudad_id)
        if ciudad_nombre is None:
            raise api_error(404, "CIUDAD_NO_ENCONTRADA", "La ciudad especificada no existe")

        # Validar nombre unico en tenant
        dup = await conn.fetchval(
            """
            SELECT id FROM sucursal
             WHERE empresa_id = $1 AND lower(nombre) = lower($2) AND deleted_at IS NULL
            """,
            UUID(empresa_id),
            data.nombre.strip(),
        )
        if dup is not None:
            raise api_error(409, "SUCURSAL_DUPLICADA", f"Ya existe una sucursal llamada '{data.nombre}'")

        if data.es_matriz:
            await conn.execute(
                "UPDATE sucursal SET es_matriz = false WHERE empresa_id = $1",
                UUID(empresa_id),
            )

        row = await conn.fetchrow(
            """
            INSERT INTO sucursal (empresa_id, ciudad_id, nombre, direccion, telefono, es_matriz, estado)
            VALUES ($1, $2, $3, $4, $5, $6, 'activa')
            RETURNING id, empresa_id, ciudad_id, nombre, direccion, telefono, es_matriz, estado, created_at, updated_at
            """,
            UUID(empresa_id),
            data.ciudad_id,
            data.nombre.strip(),
            data.direccion.strip(),
            data.telefono.strip() if data.telefono else None,
            data.es_matriz,
        )

        sucursal = SucursalOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            ciudad_id=row["ciudad_id"],
            ciudad_nombre=ciudad_nombre,
            nombre=row["nombre"],
            direccion=row["direccion"],
            telefono=row["telefono"],
            es_matriz=row["es_matriz"],
            estado=row["estado"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="sucursal",
        entidad_id=sucursal.id,
        datos_despues=data.model_dump(mode="json"),
    )
    return sucursal


async def update_sucursal(
    empresa_id: str,
    user_id: str,
    sucursal_id: str,
    data: SucursalUpdateRequest,
) -> SucursalOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        current = await conn.fetchrow(
            """
            SELECT id, ciudad_id, nombre, direccion, telefono, es_matriz, estado
              FROM sucursal
             WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL
            """,
            UUID(sucursal_id),
            UUID(empresa_id),
        )
        if current is None:
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal no existe")

        # Si se reactiva una sucursal inactiva, revalidar regla BR-02
        if data.estado == "activa" and current["estado"] == "inactiva":
            limite, _ = await get_limite_sucursales(conn, UUID(empresa_id))
            activas_actuales = await conn.fetchval(
                "SELECT count(*)::integer FROM sucursal WHERE empresa_id = $1 AND estado = 'activa' AND deleted_at IS NULL",
                UUID(empresa_id),
            )
            if activas_actuales >= limite:
                raise api_error(
                    402,
                    "LIMITE_SUCURSALES_ALCANZADO",
                    f"No puede activar la sucursal: limite maximo alcanzado ({limite}) para su plan.",
                )

        new_ciudad_id = data.ciudad_id if data.ciudad_id is not None else current["ciudad_id"]
        ciudad_nombre = await conn.fetchval("SELECT nombre FROM ciudad WHERE id = $1", new_ciudad_id)
        if ciudad_nombre is None:
            raise api_error(404, "CIUDAD_NO_ENCONTRADA", "La ciudad especificada no existe")

        new_nombre = data.nombre.strip() if data.nombre is not None else current["nombre"]
        if new_nombre.lower() != current["nombre"].lower():
            dup = await conn.fetchval(
                "SELECT id FROM sucursal WHERE empresa_id = $1 AND lower(nombre) = lower($2) AND id <> $3 AND deleted_at IS NULL",
                UUID(empresa_id),
                new_nombre,
                UUID(sucursal_id),
            )
            if dup is not None:
                raise api_error(409, "SUCURSAL_DUPLICADA", f"El nombre '{new_nombre}' ya esta en uso")

        new_es_matriz = data.es_matriz if data.es_matriz is not None else current["es_matriz"]
        if new_es_matriz and not current["es_matriz"]:
            await conn.execute("UPDATE sucursal SET es_matriz = false WHERE empresa_id = $1", UUID(empresa_id))

        new_direccion = data.direccion.strip() if data.direccion is not None else current["direccion"]
        new_telefono = data.telefono.strip() if data.telefono is not None else current["telefono"]
        new_estado = data.estado if data.estado is not None else current["estado"]

        row = await conn.fetchrow(
            """
            UPDATE sucursal
               SET ciudad_id = $1,
                   nombre = $2,
                   direccion = $3,
                   telefono = $4,
                   es_matriz = $5,
                   estado = $6,
                   updated_at = now()
             WHERE id = $7 AND empresa_id = $8
            RETURNING id, empresa_id, ciudad_id, nombre, direccion, telefono, es_matriz, estado, created_at, updated_at
            """,
            new_ciudad_id,
            new_nombre,
            new_direccion,
            new_telefono,
            new_es_matriz,
            new_estado,
            UUID(sucursal_id),
            UUID(empresa_id),
        )

        sucursal = SucursalOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            ciudad_id=row["ciudad_id"],
            ciudad_nombre=ciudad_nombre,
            nombre=row["nombre"],
            direccion=row["direccion"],
            telefono=row["telefono"],
            es_matriz=row["es_matriz"],
            estado=row["estado"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="sucursal",
        entidad_id=sucursal.id,
        datos_despues=data.model_dump(exclude_unset=True, mode="json"),
    )
    return sucursal


async def delete_sucursal(
    empresa_id: str,
    user_id: str,
    sucursal_id: str,
) -> dict[str, str]:
    async with tenant_connection(empresa_id, user_id) as conn:
        result = await conn.execute(
            """
            UPDATE sucursal
               SET deleted_at = now(),
                   estado = 'inactiva',
                   updated_at = now()
             WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL
            """,
            UUID(sucursal_id),
            UUID(empresa_id),
        )
        if result == "UPDATE 0":
            raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal no existe o ya fue eliminada")

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="delete",
        entidad="sucursal",
        entidad_id=sucursal_id,
    )
    return {"mensaje": "Sucursal dada de baja correctamente"}
