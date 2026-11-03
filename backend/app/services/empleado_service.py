import logging
from uuid import UUID

from app.core.errors import api_error
from app.core.security import hash_password
from app.db import audit_event, tenant_connection
from app.schemas.empleado import (
    EmpleadoCreateRequest,
    EmpleadoListResponse,
    EmpleadoOut,
    EmpleadoUpdateRequest,
    RolDisponibleOut,
)

logger = logging.getLogger(__name__)


async def list_roles_disponibles(empresa_id: str, user_id: str) -> list[RolDisponibleOut]:
    async with tenant_connection(empresa_id, user_id) as conn:
        rows = await conn.fetch(
            """
            SELECT id, nombre, descripcion
              FROM rol
             WHERE empresa_id = $1
               AND es_global = false
               AND lower(nombre) <> 'superadmin'
             ORDER BY nombre ASC
            """,
            UUID(empresa_id),
        )
        return [
            RolDisponibleOut(
                id=r["id"],
                nombre=r["nombre"],
                descripcion=r["descripcion"],
            )
            for r in rows
        ]


async def list_empleados(
    empresa_id: str,
    user_id: str,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> EmpleadoListResponse:
    async with tenant_connection(empresa_id, user_id) as conn:
        conditions = ["u.empresa_id = $1", "u.deleted_at IS NULL"]
        params: list[object] = [UUID(empresa_id)]

        if search:
            params.append(f"%{search.strip().lower()}%")
            conditions.append(f"(lower(u.nombre) LIKE ${len(params)} OR lower(u.correo) LIKE ${len(params)})")

        where_clause = " AND ".join(conditions)

        total = await conn.fetchval(
            f"SELECT count(*)::integer FROM usuario u WHERE {where_clause}",
            *params,
        )

        params.extend([limit, offset])
        rows = await conn.fetch(
            f"""
            SELECT u.id,
                   u.empresa_id,
                   u.nombre,
                   u.correo,
                   r.nombre AS rol_nombre,
                   u.sucursal_id,
                   s.nombre AS sucursal_nombre,
                   u.telefono,
                   u.estado,
                   u.ultimo_acceso,
                   u.created_at
              FROM usuario u
              JOIN rol r ON r.id = u.rol_id
              LEFT JOIN sucursal s ON s.id = u.sucursal_id
             WHERE {where_clause}
             ORDER BY u.created_at DESC
             LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

        items = [
            EmpleadoOut(
                id=r["id"],
                empresa_id=r["empresa_id"],
                nombre=r["nombre"],
                correo=r["correo"],
                rol_nombre=r["rol_nombre"],
                sucursal_id=r["sucursal_id"],
                sucursal_nombre=r["sucursal_nombre"],
                telefono=r["telefono"],
                estado=r["estado"],
                ultimo_acceso=r["ultimo_acceso"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
        return EmpleadoListResponse(total=total, items=items)


async def get_empleado(empresa_id: str, user_id: str, empleado_id: str) -> EmpleadoOut:
    async with tenant_connection(empresa_id, user_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT u.id,
                   u.empresa_id,
                   u.nombre,
                   u.correo,
                   r.nombre AS rol_nombre,
                   u.sucursal_id,
                   s.nombre AS sucursal_nombre,
                   u.telefono,
                   u.estado,
                   u.ultimo_acceso,
                   u.created_at
              FROM usuario u
              JOIN rol r ON r.id = u.rol_id
              LEFT JOIN sucursal s ON s.id = u.sucursal_id
             WHERE u.id = $1
               AND u.empresa_id = $2
               AND u.deleted_at IS NULL
            """,
            UUID(empleado_id),
            UUID(empresa_id),
        )
        if row is None:
            raise api_error(404, "EMPLEADO_NO_ENCONTRADO", "El empleado no existe en su empresa")

        return EmpleadoOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            correo=row["correo"],
            rol_nombre=row["rol_nombre"],
            sucursal_id=row["sucursal_id"],
            sucursal_nombre=row["sucursal_nombre"],
            telefono=row["telefono"],
            estado=row["estado"],
            ultimo_acceso=row["ultimo_acceso"],
            created_at=row["created_at"],
        )


async def create_empleado(
    empresa_id: str,
    user_id: str,
    data: EmpleadoCreateRequest,
) -> EmpleadoOut:
    # Regla BR-12: Un Administrador de Empresa no puede asignar el rol superadmin
    rol_solicitado = data.rol.strip().lower()
    if rol_solicitado == "superadmin":
        raise api_error(
            403,
            "ROL_NO_PERMITIDO",
            "Regla BR-12: Un Administrador de Empresa no puede asignar el rol superadmin",
        )

    async with tenant_connection(empresa_id, user_id) as conn:
        # Validar existencia del rol en el tenant
        rol_row = await conn.fetchrow(
            """
            SELECT id, nombre
              FROM rol
             WHERE empresa_id = $1
               AND lower(nombre) = lower($2)
            """,
            UUID(empresa_id),
            rol_solicitado,
        )
        if rol_row is None:
            raise api_error(
                404,
                "ROL_NO_ENCONTRADO",
                f"El rol '{data.rol}' no existe para su empresa",
            )
        rol_id = rol_row["id"]

        # Validar sucursal asignada si viene provista
        sucursal_nombre = None
        if data.sucursal_id is not None:
            sucursal_nombre = await conn.fetchval(
                """
                SELECT nombre
                  FROM sucursal
                 WHERE id = $1
                   AND empresa_id = $2
                   AND deleted_at IS NULL
                """,
                data.sucursal_id,
                UUID(empresa_id),
            )
            if sucursal_nombre is None:
                raise api_error(
                    404,
                    "SUCURSAL_NO_ENCONTRADA",
                    "La sucursal asignada no existe o no pertenece a su empresa",
                )

        # Validar unicidad de correo en la empresa
        correo_limpio = data.correo.strip().lower()
        existe_correo = await conn.fetchval(
            """
            SELECT id
              FROM usuario
             WHERE empresa_id = $1
               AND lower(correo) = lower($2)
               AND deleted_at IS NULL
            """,
            UUID(empresa_id),
            correo_limpio,
        )
        if existe_correo is not None:
            raise api_error(
                409,
                "CORREO_DUPLICADO",
                f"El correo '{data.correo}' ya esta en uso en su empresa",
            )

        pwd_hash = hash_password(data.password)

        row = await conn.fetchrow(
            """
            INSERT INTO usuario (
                empresa_id, rol_id, sucursal_id, nombre, correo, password_hash,
                telefono, email_verificado, email_verificado_en, estado
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, true, now(), 'activo')
            RETURNING id, empresa_id, nombre, correo, telefono, estado, created_at
            """,
            UUID(empresa_id),
            rol_id,
            data.sucursal_id,
            data.nombre.strip(),
            correo_limpio,
            pwd_hash,
            data.telefono.strip() if data.telefono else None,
        )

        empleado = EmpleadoOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            correo=row["correo"],
            rol_nombre=rol_row["nombre"],
            sucursal_id=data.sucursal_id,
            sucursal_nombre=sucursal_nombre,
            telefono=row["telefono"],
            estado=row["estado"],
            ultimo_acceso=None,
            created_at=row["created_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="usuario",
        entidad_id=empleado.id,
        datos_despues={
            "nombre": empleado.nombre,
            "correo": empleado.correo,
            "rol": empleado.rol_nombre,
            "sucursal_id": str(empleado.sucursal_id) if empleado.sucursal_id else None,
        },
    )
    return empleado


async def update_empleado(
    empresa_id: str,
    user_id: str,
    empleado_id: str,
    data: EmpleadoUpdateRequest,
) -> EmpleadoOut:
    if data.rol and data.rol.strip().lower() == "superadmin":
        raise api_error(
            403,
            "ROL_NO_PERMITIDO",
            "Regla BR-12: Un Administrador de Empresa no puede asignar el rol superadmin",
        )

    async with tenant_connection(empresa_id, user_id) as conn:
        current = await conn.fetchrow(
            """
            SELECT u.id, u.nombre, u.correo, u.rol_id, u.sucursal_id, u.telefono, u.estado
              FROM usuario u
             WHERE u.id = $1 AND u.empresa_id = $2 AND u.deleted_at IS NULL
            """,
            UUID(empleado_id),
            UUID(empresa_id),
        )
        if current is None:
            raise api_error(404, "EMPLEADO_NO_ENCONTRADO", "El empleado no existe")

        new_rol_id = current["rol_id"]
        if data.rol:
            rol_row = await conn.fetchrow(
                "SELECT id, nombre FROM rol WHERE empresa_id = $1 AND lower(nombre) = lower($2)",
                UUID(empresa_id),
                data.rol.strip().lower(),
            )
            if rol_row is None:
                raise api_error(404, "ROL_NO_ENCONTRADO", f"El rol '{data.rol}' no existe")
            new_rol_id = rol_row["id"]

        new_sucursal_id = data.sucursal_id if data.sucursal_id is not None else current["sucursal_id"]
        if data.sucursal_id is not None:
            valid_suc = await conn.fetchval(
                "SELECT id FROM sucursal WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL",
                data.sucursal_id,
                UUID(empresa_id),
            )
            if valid_suc is None:
                raise api_error(404, "SUCURSAL_NO_ENCONTRADA", "La sucursal asignada no existe")

        new_nombre = data.nombre.strip() if data.nombre is not None else current["nombre"]
        new_telefono = data.telefono.strip() if data.telefono is not None else current["telefono"]
        new_estado = data.estado if data.estado is not None else current["estado"]

        await conn.execute(
            """
            UPDATE usuario
               SET nombre = $1,
                   rol_id = $2,
                   sucursal_id = $3,
                   telefono = $4,
                   estado = $5,
                   updated_at = now()
             WHERE id = $6 AND empresa_id = $7
            """,
            new_nombre,
            new_rol_id,
            new_sucursal_id,
            new_telefono,
            new_estado,
            UUID(empleado_id),
            UUID(empresa_id),
        )

        row = await conn.fetchrow(
            """
            SELECT u.id, u.empresa_id, u.nombre, u.correo, r.nombre AS rol_nombre,
                   u.sucursal_id, s.nombre AS sucursal_nombre, u.telefono, u.estado,
                   u.ultimo_acceso, u.created_at
              FROM usuario u
              JOIN rol r ON r.id = u.rol_id
              LEFT JOIN sucursal s ON s.id = u.sucursal_id
             WHERE u.id = $1
            """,
            UUID(empleado_id),
        )

        empleado = EmpleadoOut(
            id=row["id"],
            empresa_id=row["empresa_id"],
            nombre=row["nombre"],
            correo=row["correo"],
            rol_nombre=row["rol_nombre"],
            sucursal_id=row["sucursal_id"],
            sucursal_nombre=row["sucursal_nombre"],
            telefono=row["telefono"],
            estado=row["estado"],
            ultimo_acceso=row["ultimo_acceso"],
            created_at=row["created_at"],
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="update",
        entidad="usuario",
        entidad_id=empleado.id,
        datos_despues=data.model_dump(exclude_unset=True, mode="json"),
    )
    return empleado


async def delete_empleado(
    empresa_id: str,
    user_id: str,
    empleado_id: str,
) -> dict[str, str]:
    if empleado_id == user_id:
        raise api_error(400, "OPERACION_INVALIDA", "No puede auto-eliminar su propia cuenta de usuario")

    async with tenant_connection(empresa_id, user_id) as conn:
        result = await conn.execute(
            """
            UPDATE usuario
               SET deleted_at = now(),
                   estado = 'inactivo',
                   updated_at = now()
             WHERE id = $1 AND empresa_id = $2 AND deleted_at IS NULL
            """,
            UUID(empleado_id),
            UUID(empresa_id),
        )
        if result == "UPDATE 0":
            raise api_error(404, "EMPLEADO_NO_ENCONTRADO", "El empleado no existe o ya fue eliminado")

        # Revocar sesiones del empleado
        await conn.execute(
            "UPDATE sesion SET revocado_en = now() WHERE usuario_id = $1 AND revocado_en IS NULL",
            UUID(empleado_id),
        )

    await audit_event(
        empresa_id=empresa_id,
        usuario_id=user_id,
        actor_tipo="usuario",
        accion="delete",
        entidad="usuario",
        entidad_id=empleado_id,
    )
    return {"mensaje": "Empleado dado de baja y sesiones revocadas correctamente"}
