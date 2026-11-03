import logging
from uuid import UUID

from app.core.errors import api_error
from app.db import audit_event, tenant_connection
from app.schemas.coleccion import (
    ColeccionCreateRequest,
    ColeccionOut,
    ColeccionUpdateRequest,
    TemporadaCreateRequest,
    TemporadaOut,
    TemporadaUpdateRequest,
    TemporadasColeccionesResponse,
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# TEMPORADAS
# ----------------------------------------------------

async def list_temporadas(empresa_id: str, user_id: str) -> list[TemporadaOut]:
    async with tenant_connection(empresa_id, user_id) as conn:
        rows = await conn.fetch(
            """
            SELECT id, empresa_id, nombre, fecha_inicio, fecha_fin, created_at, updated_at
              FROM temporada
             WHERE empresa_id = $1
             ORDER BY fecha_inicio DESC NULLS LAST, nombre ASC
            """,
            UUID(empresa_id),
        )
        return [
            TemporadaOut(
                id=r["id"],
                empresa_id=r["empresa_id"],
                nombre=r["nombre"],
                fecha_inicio=r["fecha_inicio"],
                fecha_fin=r["fecha_fin"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


async def create_temporada(
    empresa_id: str,
    user_id: str,
    data: TemporadaCreateRequest,
) -> TemporadaOut:
    if data.fecha_inicio and data.fecha_fin and data.fecha_inicio >= data.fecha_fin:
        raise api_error(
            422,
            "RANGO_FECHAS_INVALIDO",
            "La fecha de inicio debe ser estrictamente anterior a la fecha de finalizacion",
        )

    async with tenant_connection(empresa_id, user_id) as conn:
        existing = await conn.fetchval(
            """
            SELECT id FROM temporada
             WHERE empresa_id = $1 AND lower(nombre) = lower($2)
            """,
            UUID(empresa_id),
            data.nombre.strip(),
        )
        if existing is not None:
            raise api_error(
                409,
                "TEMPORADA_DUPLICADA",
                f"Ya existe una temporada con el nombre '{data.nombre}' en esta empresa",
            )

        row = await conn.fetchrow(
            """
            INSERT INTO temporada (empresa_id, nombre, fecha_inicio, fecha_fin)
            VALUES ($1, $2, $3, $4)
            RETURNING id, empresa_id, nombre, fecha_inicio, fecha_fin, created_at, updated_at
            """,
            UUID(empresa_id),
            data.nombre.strip(),
            data.fecha_inicio,
            data.fecha_fin,
        )
        temporada = TemporadaOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            fecha_inicio=row["fecha_inicio"],
            fecha_fin=row["fecha_fin"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="temporada",
        entidad_id=temporada.id,
        datos_despues=data.model_dump(mode="json"),
    )
    return temporada


async def update_temporada(
    empresa_id: str,
    user_id: str,
    temporada_id: str,
    data: TemporadaUpdateRequest,
) -> TemporadaOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        current = await conn.fetchrow(
            """
            SELECT id, nombre, fecha_inicio, fecha_fin
              FROM temporada
             WHERE id = $1 AND empresa_id = $2
            """,
            UUID(temporada_id),
            UUID(empresa_id),
        )
        if current is None:
            raise api_error(404, "TEMPORADA_NO_ENCONTRADA", "La temporada no existe")

        new_inicio = data.fecha_inicio if data.fecha_inicio is not None else current["fecha_inicio"]
        new_fin = data.fecha_fin if data.fecha_fin is not None else current["fecha_fin"]
        if new_inicio and new_fin and new_inicio >= new_fin:
            raise api_error(
                422,
                "RANGO_FECHAS_INVALIDO",
                "La fecha de inicio debe ser estrictamente anterior a la fecha de finalizacion",
            )

        new_nombre = data.nombre.strip() if data.nombre is not None else current["nombre"]
        if new_nombre.lower() != current["nombre"].lower():
            conflict = await conn.fetchval(
                """
                SELECT id FROM temporada
                 WHERE empresa_id = $1 AND lower(nombre) = lower($2) AND id <> $3
                """,
                UUID(empresa_id),
                new_nombre,
                UUID(temporada_id),
            )
            if conflict is not None:
                raise api_error(409, "TEMPORADA_DUPLICADA", f"El nombre '{new_nombre}' ya esta en uso")

        row = await conn.fetchrow(
            """
            UPDATE temporada
               SET nombre = $1,
                   fecha_inicio = $2,
                   fecha_fin = $3,
                   updated_at = now()
             WHERE id = $4 AND empresa_id = $5
            RETURNING id, empresa_id, nombre, fecha_inicio, fecha_fin, created_at, updated_at
            """,
            new_nombre,
            new_inicio,
            new_fin,
            UUID(temporada_id),
            UUID(empresa_id),
        )
        temporada = TemporadaOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            fecha_inicio=row["fecha_inicio"],
            fecha_fin=row["fecha_fin"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="temporada",
        entidad_id=temporada.id,
        datos_despues=data.model_dump(exclude_unset=True, mode="json"),
    )
    return temporada


async def delete_temporada(
    empresa_id: str,
    user_id: str,
    temporada_id: str,
) -> dict[str, str]:
    async with tenant_connection(empresa_id, user_id) as conn:
        # Verificar si hay prendas vinculadas
        prendas_count = await conn.fetchval(
            "SELECT count(*)::integer FROM prenda WHERE temporada_id = $1 AND empresa_id = $2",
            UUID(temporada_id),
            UUID(empresa_id),
        )
        if prendas_count > 0:
            raise api_error(
                400,
                "TEMPORADA_EN_USO",
                f"No se puede eliminar la temporada porque tiene {prendas_count} prendas asociadas",
            )

        result = await conn.execute(
            "DELETE FROM temporada WHERE id = $1 AND empresa_id = $2",
            UUID(temporada_id),
            UUID(empresa_id),
        )
        if result == "DELETE 0":
            raise api_error(404, "TEMPORADA_NO_ENCONTRADA", "La temporada no existe")

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="delete",
        entidad="temporada",
        entidad_id=temporada_id,
    )
    return {"mensaje": "Temporada eliminada correctamente"}


# ----------------------------------------------------
# COLECCIONES
# ----------------------------------------------------

async def list_colecciones(empresa_id: str, user_id: str) -> list[ColeccionOut]:
    async with tenant_connection(empresa_id, user_id) as conn:
        rows = await conn.fetch(
            """
            SELECT id, empresa_id, nombre, anio, created_at, updated_at
              FROM coleccion
             WHERE empresa_id = $1
             ORDER BY anio DESC NULLS LAST, nombre ASC
            """,
            UUID(empresa_id),
        )
        return [
            ColeccionOut(
                id=r["id"],
                empresa_id=r["empresa_id"],
                nombre=r["nombre"],
                anio=r["anio"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


async def create_coleccion(
    empresa_id: str,
    user_id: str,
    data: ColeccionCreateRequest,
) -> ColeccionOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        existing = await conn.fetchval(
            """
            SELECT id FROM coleccion
             WHERE empresa_id = $1 AND lower(nombre) = lower($2)
            """,
            UUID(empresa_id),
            data.nombre.strip(),
        )
        if existing is not None:
            raise api_error(
                409,
                "COLECCION_DUPLICADA",
                f"Ya existe una coleccion con el nombre '{data.nombre}' en esta empresa",
            )

        row = await conn.fetchrow(
            """
            INSERT INTO coleccion (empresa_id, nombre, anio)
            VALUES ($1, $2, $3)
            RETURNING id, empresa_id, nombre, anio, created_at, updated_at
            """,
            UUID(empresa_id),
            data.nombre.strip(),
            data.anio,
        )
        coleccion = ColeccionOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            anio=row["anio"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="coleccion",
        entidad_id=coleccion.id,
        datos_despues=data.model_dump(mode="json"),
    )
    return coleccion


async def update_coleccion(
    empresa_id: str,
    user_id: str,
    coleccion_id: str,
    data: ColeccionUpdateRequest,
) -> ColeccionOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        current = await conn.fetchrow(
            """
            SELECT id, nombre, anio
              FROM coleccion
             WHERE id = $1 AND empresa_id = $2
            """,
            UUID(coleccion_id),
            UUID(empresa_id),
        )
        if current is None:
            raise api_error(404, "COLECCION_NO_ENCONTRADA", "La coleccion no existe")

        new_nombre = data.nombre.strip() if data.nombre is not None else current["nombre"]
        if new_nombre.lower() != current["nombre"].lower():
            conflict = await conn.fetchval(
                """
                SELECT id FROM coleccion
                 WHERE empresa_id = $1 AND lower(nombre) = lower($2) AND id <> $3
                """,
                UUID(empresa_id),
                new_nombre,
                UUID(coleccion_id),
            )
            if conflict is not None:
                raise api_error(409, "COLECCION_DUPLICADA", f"El nombre '{new_nombre}' ya esta en uso")

        new_anio = data.anio if data.anio is not None else current["anio"]

        row = await conn.fetchrow(
            """
            UPDATE coleccion
               SET nombre = $1,
                   anio = $2,
                   updated_at = now()
             WHERE id = $3 AND empresa_id = $4
            RETURNING id, empresa_id, nombre, anio, created_at, updated_at
            """,
            new_nombre,
            new_anio,
            UUID(coleccion_id),
            UUID(empresa_id),
        )
        coleccion = ColeccionOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            anio=row["anio"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="coleccion",
        entidad_id=coleccion.id,
        datos_despues=data.model_dump(exclude_unset=True, mode="json"),
    )
    return coleccion


async def delete_coleccion(
    empresa_id: str,
    user_id: str,
    coleccion_id: str,
) -> dict[str, str]:
    async with tenant_connection(empresa_id, user_id) as conn:
        prendas_count = await conn.fetchval(
            "SELECT count(*)::integer FROM prenda WHERE coleccion_id = $1 AND empresa_id = $2",
            UUID(coleccion_id),
            UUID(empresa_id),
        )
        if prendas_count > 0:
            raise api_error(
                400,
                "COLECCION_EN_USO",
                f"No se puede eliminar la coleccion porque tiene {prendas_count} prendas asociadas",
            )

        result = await conn.execute(
            "DELETE FROM coleccion WHERE id = $1 AND empresa_id = $2",
            UUID(coleccion_id),
            UUID(empresa_id),
        )
        if result == "DELETE 0":
            raise api_error(404, "COLECCION_NO_ENCONTRADA", "La coleccion no existe")

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="delete",
        entidad="coleccion",
        entidad_id=coleccion_id,
    )
    return {"mensaje": "Coleccion eliminada correctamente"}


async def get_resumen_temporadas_colecciones(
    empresa_id: str,
    user_id: str,
) -> TemporadasColeccionesResponse:
    temporadas = await list_temporadas(empresa_id, user_id)
    colecciones = await list_colecciones(empresa_id, user_id)
    return TemporadasColeccionesResponse(temporadas=temporadas, colecciones=colecciones)
