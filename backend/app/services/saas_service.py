import logging
import re
import secrets
import unicodedata
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.core.errors import api_error
from app.core.security import hash_password
from app.db import admin_connection, audit_event, tenant_connection
from app.schemas.saas import (
    EmpresaCreateRequest,
    EmpresaCreateResponse,
    EmpresaListResponse,
    EmpresaResumen,
    EstadoEmpresaResponse,
    MetricasSaaSOut,
    MiSuscripcionOut,
    PlanOut,
    SuscripcionOut,
    SuscripcionUpsertRequest,
)

logger = logging.getLogger(__name__)

_EMPRESA_COLUMNS = """
       e.id,
       e.nombre,
       e.slug,
       e.nit,
       e.correo,
       e.telefono,
       e.direccion,
       e.estado,
       e.created_at,
       s.id AS suscripcion_id,
       s.plan_id,
       s.estado AS suscripcion_estado,
       s.fecha_inicio AS suscripcion_fecha_inicio,
       s.fecha_fin AS suscripcion_fecha_fin,
       s.renovacion_auto,
       p.codigo AS plan_codigo,
       p.nombre AS plan_nombre,
       p.precio_mensual,
       p.moneda,
       (
           SELECT count(*)::integer
             FROM sucursal su
            WHERE su.empresa_id = e.id
              AND su.estado = 'activa'
              AND su.deleted_at IS NULL
       ) AS sucursales_activas
"""

_EMPRESA_FROM = """
  FROM empresa e
  LEFT JOIN LATERAL (
      SELECT s2.id,
             s2.plan_id,
             s2.estado,
             s2.fecha_inicio,
             s2.fecha_fin,
             s2.renovacion_auto
        FROM suscripcion s2
       WHERE s2.empresa_id = e.id
       ORDER BY s2.fecha_inicio DESC, s2.created_at DESC
       LIMIT 1
  ) s ON true
  LEFT JOIN plan p ON p.id = s.plan_id
"""

_EMPRESA_SELECT = f"SELECT {_EMPRESA_COLUMNS} {_EMPRESA_FROM}"

_ROLE_DEFINITIONS = (
    ("administrador", "Acceso total al tenant", None),
    (
        "encargado",
        "Encargado de sucursal",
        ("ventas.crear", "ventas.ver", "inventario.ver", "inventario.ajustar", "catalogo.ver"),
    ),
    ("cajero", "Operacion de ventas", ("ventas.crear", "ventas.ver", "inventario.ver", "catalogo.ver")),
    ("cliente", "Cliente de la tienda en linea", ("catalogo.ver", "ventas.ver")),
)


def _value(row: Any, key: str, default: Any = None) -> Any:
    return row[key] if key in row.keys() else default


async def _safe_audit(**kwargs: Any) -> None:
    try:
        await audit_event(**kwargs)
    except Exception:
        logger.exception("No se pudo registrar el evento de auditoria SaaS")


def _slug_base(nombre: str) -> str:
    normalized = unicodedata.normalize("NFKD", nombre)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name.lower()).strip("-")
    return (slug or "empresa")[:80]


async def _unique_slug(conn: Any, nombre: str) -> str:
    base = _slug_base(nombre)
    candidate = base
    suffix = 2
    while await conn.fetchval("SELECT 1 FROM empresa WHERE slug = $1", candidate):
        candidate = f"{base[:72]}-{suffix}"
        suffix += 1
    return candidate


async def _limits_by_plan(conn: Any) -> dict[int, dict[str, int | None]]:
    rows = await conn.fetch("SELECT plan_id, recurso, limite FROM plan_limite")
    limits: dict[int, dict[str, int | None]] = {}
    for row in rows:
        limits.setdefault(int(row["plan_id"]), {})[row["recurso"]] = row["limite"]
    return limits


def _ia_habilitada(limites: dict[str, int | None]) -> bool:
    if "consultas_ia_mes" not in limites:
        return False
    limite = limites["consultas_ia_mes"]
    return limite is None or limite > 0


def _suscripcion_out(
    row: Any,
    limites: dict[str, int | None],
    sucursales_activas: int,
) -> SuscripcionOut | None:
    suscripcion_id = _value(row, "suscripcion_id")
    if suscripcion_id is None:
        return None

    fecha_fin = _value(row, "suscripcion_fecha_fin")
    dias_restantes = (fecha_fin - date.today()).days if fecha_fin is not None else None
    por_vencer = dias_restantes is not None and 0 <= dias_restantes <= 7

    plan = PlanOut(
        codigo=_value(row, "plan_codigo", ""),
        nombre=_value(row, "plan_nombre", ""),
        precio_mensual=Decimal(str(_value(row, "precio_mensual", 0))),
        moneda=_value(row, "moneda", "BOB"),
        limites=limites,
    )
    return SuscripcionOut(
        id=suscripcion_id,
        plan=plan,
        estado=_value(row, "suscripcion_estado", ""),
        fecha_inicio=_value(row, "suscripcion_fecha_inicio"),
        fecha_fin=fecha_fin,
        renovacion_auto=bool(_value(row, "renovacion_auto", False)),
        dias_restantes=dias_restantes,
        por_vencer=por_vencer,
        limites=limites,
        uso={"sucursales": sucursales_activas},
        ia_habilitada=_ia_habilitada(limites),
    )


def _empresa_out(row: Any, limits: dict[int, dict[str, int | None]]) -> EmpresaResumen:
    sucursales_activas = int(_value(row, "sucursales_activas", 0) or 0)
    plan_id = _value(row, "plan_id")
    limites = limits.get(int(plan_id), {}) if plan_id is not None else {}
    return EmpresaResumen(
        id=row["id"],
        nombre=row["nombre"],
        slug=str(row["slug"]),
        nit=row["nit"],
        correo=str(row["correo"]),
        telefono=row["telefono"],
        direccion=row["direccion"],
        estado=row["estado"],
        created_at=row["created_at"],
        sucursales_activas=sucursales_activas,
        suscripcion=_suscripcion_out(row, limites, sucursales_activas),
    )


def _mi_suscripcion_out(
    row: Any,
    limits: dict[int, dict[str, int | None]],
) -> MiSuscripcionOut:
    sucursales_activas = int(_value(row, "sucursales_activas", 0) or 0)
    plan_id = _value(row, "plan_id")
    limites = limits.get(int(plan_id), {}) if plan_id is not None else {}
    suscripcion = _suscripcion_out(row, limites, sucursales_activas)
    if suscripcion is None:
        raise api_error(404, "SUSCRIPCION_NO_ENCONTRADA", "La empresa no tiene una suscripcion registrada")
    return MiSuscripcionOut(
        empresa_id=row["id"],
        empresa_nombre=row["nombre"],
        suscripcion=suscripcion,
    )


def _plan_out(plan: Any, limites: dict[str, int | None]) -> PlanOut:
    return PlanOut(
        codigo=plan["codigo"],
        nombre=plan["nombre"],
        precio_mensual=plan["precio_mensual"],
        moneda=plan["moneda"],
        limites=limites,
    )


def _suscripcion_data(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "estado": row["estado"],
        "plan_id": row["plan_id"],
        "fecha_inicio": str(row["fecha_inicio"]),
        "fecha_fin": str(row["fecha_fin"]) if row["fecha_fin"] is not None else None,
        "renovacion_auto": row["renovacion_auto"],
    }


async def _revoke_sessions(conn: Any, empresa_id: Any) -> None:
    await conn.execute(
        "UPDATE sesion SET revocado_en = now() WHERE empresa_id = $1 AND revocado_en IS NULL",
        empresa_id,
    )


async def list_planes() -> list[PlanOut]:
    async with admin_connection() as conn:
        planes = await conn.fetch(
            "SELECT id, codigo, nombre, precio_mensual, moneda FROM plan WHERE activo ORDER BY precio_mensual"
        )
        limits = await _limits_by_plan(conn)

    return [_plan_out(plan, limits.get(int(plan["id"]), {})) for plan in planes]


async def list_empresas(
    *,
    search: str | None,
    estado: str | None,
    plan: str | None,
    por_vencer: bool,
    page: int,
    page_size: int,
) -> EmpresaListResponse:
    where = ["e.deleted_at IS NULL"]
    params: list[Any] = []

    if search and search.strip():
        params.append(f"%{search.strip()}%")
        idx = len(params)
        where.append(
            f"(e.nombre ILIKE ${idx} OR e.nit ILIKE ${idx} OR e.slug::text ILIKE ${idx})"
        )

    if estado:
        params.append(estado)
        where.append(f"e.estado = ${len(params)}")

    if plan:
        params.append(plan.strip().lower())
        where.append(f"p.codigo = ${len(params)}")

    if por_vencer:
        where.append(
            "s.fecha_fin IS NOT NULL "
            "AND s.fecha_fin BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 "
            "AND s.estado IN ('prueba', 'activa', 'mora')"
        )

    where_sql = f"WHERE {' AND '.join(where)}"

    async with admin_connection() as conn:
        total = int(
            await conn.fetchval(
                f"SELECT count(*) {_EMPRESA_FROM} {where_sql}", *params
            )
            or 0
        )
        limit_idx = len(params) + 1
        offset_idx = len(params) + 2
        rows = await conn.fetch(
            f"""
            {_EMPRESA_SELECT}
            {where_sql}
             ORDER BY e.created_at DESC, e.nombre
             LIMIT ${limit_idx} OFFSET ${offset_idx}
            """,
            *params,
            page_size,
            (page - 1) * page_size,
        )
        limits = await _limits_by_plan(conn)

    return EmpresaListResponse(
        items=[_empresa_out(row, limits) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_empresa(empresa_id: str) -> EmpresaResumen:
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            f"{_EMPRESA_SELECT} WHERE e.id = $1 AND e.deleted_at IS NULL",
            empresa_id,
        )
        limits = await _limits_by_plan(conn)

    if row is None:
        raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
    return _empresa_out(row, limits)


async def get_mi_suscripcion(empresa_id: str, usuario_id: str) -> MiSuscripcionOut:
    async with tenant_connection(empresa_id, usuario_id) as conn:
        row = await conn.fetchrow(
            f"{_EMPRESA_SELECT} WHERE e.id = $1 AND e.deleted_at IS NULL",
            empresa_id,
        )
        limits = await _limits_by_plan(conn)

    if row is None:
        raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
    return _mi_suscripcion_out(row, limits)


async def get_empresa_suscripcion(empresa_id: str) -> MiSuscripcionOut:
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            f"{_EMPRESA_SELECT} WHERE e.id = $1 AND e.deleted_at IS NULL",
            empresa_id,
        )
        limits = await _limits_by_plan(conn)

    if row is None:
        raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
    return _mi_suscripcion_out(row, limits)


async def create_empresa(
    data: EmpresaCreateRequest,
    *,
    actor_id: str,
    ip: str | None,
) -> EmpresaCreateResponse:
    nit = data.nit.strip().upper()
    correo_admin = str(data.correo_admin).strip().lower()
    password_temporal = secrets.token_urlsafe(9)

    async with admin_connection() as conn:
        await conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
            f"nit:{nit}",
        )
        await conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
            f"email:{correo_admin}",
        )

        if await conn.fetchval("SELECT 1 FROM empresa WHERE nit = $1", nit):
            raise api_error(409, "NIT_DUPLICADO", "Ya existe una empresa con ese NIT")

        if await conn.fetchval(
            "SELECT 1 FROM usuario WHERE correo = $1 AND deleted_at IS NULL",
            correo_admin,
        ):
            raise api_error(
                409,
                "CORREO_ADMIN_DUPLICADO",
                "Ya existe un usuario con ese correo",
            )

        slug = await _unique_slug(conn, data.nombre)

        empresa = await conn.fetchrow(
            """
            INSERT INTO empresa (nombre, slug, nit, correo, telefono, direccion, estado)
            VALUES ($1, $2, $3, $4, $5, $6, 'pendiente_plan')
            RETURNING id, nombre, slug, nit, estado
            """,
            data.nombre,
            slug,
            nit,
            correo_admin,
            data.telefono,
            data.direccion,
        )
        empresa_id = empresa["id"]

        role_ids: dict[str, Any] = {}
        for role_name, description, permissions in _ROLE_DEFINITIONS:
            role_id = await conn.fetchval(
                """
                INSERT INTO rol (empresa_id, nombre, descripcion, es_global)
                VALUES ($1, $2, $3, false)
                ON CONFLICT (empresa_id, nombre)
                DO UPDATE SET descripcion = EXCLUDED.descripcion
                RETURNING id
                """,
                empresa_id,
                role_name,
                description,
            )
            role_ids[role_name] = role_id

            if permissions is None:
                await conn.execute(
                    """
                    INSERT INTO rol_permiso (rol_id, permiso_id)
                    SELECT $1, id FROM permiso
                    ON CONFLICT DO NOTHING
                    """,
                    role_id,
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO rol_permiso (rol_id, permiso_id)
                    SELECT $1, id FROM permiso WHERE codigo = ANY($2::text[])
                    ON CONFLICT DO NOTHING
                    """,
                    role_id,
                    list(permissions),
                )

        admin_usuario_id = await conn.fetchval(
            """
            INSERT INTO usuario (
                empresa_id, rol_id, nombre, correo, password_hash,
                telefono, email_verificado, estado
            )
            VALUES ($1, $2, $3, $4, $5, NULL, true, 'activo')
            RETURNING id
            """,
            empresa_id,
            role_ids["administrador"],
            data.nombre_admin,
            correo_admin,
            hash_password(password_temporal),
        )

    await _safe_audit(
        empresa_id=None,
        empresa_afectada_id=empresa_id,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="insert",
        entidad="empresa",
        entidad_id=empresa_id,
        datos_despues={
            "nombre": data.nombre,
            "slug": slug,
            "nit": nit,
            "correo": correo_admin,
            "estado": "pendiente_plan",
            "admin_correo": correo_admin,
        },
        ip=ip,
        es_accion_superadmin=True,
        metodo="POST",
        endpoint="/api/v1/saas/empresas",
        parametros={"nit": nit, "slug": slug, "correo_admin": correo_admin},
    )

    return EmpresaCreateResponse(
        mensaje="Empresa creada. Asigne un plan para habilitar el acceso.",
        empresa_id=empresa_id,
        slug=str(empresa["slug"]),
        nombre=empresa["nombre"],
        nit=empresa["nit"],
        estado=empresa["estado"],
        admin_usuario_id=admin_usuario_id,
        admin_correo=correo_admin,
        password_temporal=password_temporal,
    )


async def assign_suscripcion(
    empresa_id: str,
    data: SuscripcionUpsertRequest,
    *,
    actor_id: str,
    ip: str | None,
) -> MiSuscripcionOut:
    async with admin_connection() as conn:
        empresa = await conn.fetchrow(
            """
            SELECT id, nombre, estado
              FROM empresa
             WHERE id = $1 AND deleted_at IS NULL
             FOR UPDATE
            """,
            empresa_id,
        )
        if empresa is None:
            raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
        if empresa["estado"] == "cancelada":
            raise api_error(409, "EMPRESA_CANCELADA", "La empresa esta cancelada")

        plan = await conn.fetchrow(
            "SELECT id, codigo, nombre FROM plan WHERE codigo = $1 AND activo",
            data.plan_codigo,
        )
        if plan is None:
            raise api_error(404, "PLAN_NO_DISPONIBLE", "El plan solicitado no esta disponible")

        limits = await _limits_by_plan(conn)
        limite_sucursales = limits.get(int(plan["id"]), {}).get("sucursales")
        sucursales_activas = int(
            await conn.fetchval(
                """
                SELECT count(*)
                  FROM sucursal
                 WHERE empresa_id = $1
                   AND estado = 'activa'
                   AND deleted_at IS NULL
                """,
                empresa_id,
            )
            or 0
        )

        if limite_sucursales is not None and sucursales_activas > limite_sucursales:
            excedente = sucursales_activas - limite_sucursales
            raise api_error(
                409,
                "LIMITE_SUCURSALES_EXCEDIDO",
                (
                    f"El plan {data.plan_codigo} permite {limite_sucursales} sucursales "
                    f"y la empresa tiene {sucursales_activas} activas. "
                    f"Desactive {excedente} sucursal(es) antes de reducir el plan."
                ),
            )

        current = await conn.fetchrow(
            """
            SELECT id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
              FROM suscripcion
             WHERE empresa_id = $1
               AND estado <> 'cancelada'
             ORDER BY fecha_inicio DESC, created_at DESC
             LIMIT 1
             FOR UPDATE
            """,
            empresa_id,
        )
        before = _suscripcion_data(current)

        await conn.execute(
            """
            UPDATE suscripcion
               SET estado = 'cancelada',
                   updated_at = now()
             WHERE empresa_id = $1
               AND estado <> 'cancelada'
            """,
            empresa_id,
        )

        suscripcion_id = await conn.fetchval(
            """
            INSERT INTO suscripcion (
                empresa_id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            empresa_id,
            plan["id"],
            data.estado,
            data.fecha_inicio,
            data.fecha_fin,
            data.renovacion_auto,
        )

        if data.estado in ("prueba", "activa", "mora"):
            empresa_estado = "activa"
        elif data.estado == "suspendida":
            empresa_estado = "suspendida"
        else:
            empresa_estado = "cancelada"

        await conn.execute(
            "UPDATE empresa SET estado = $2, updated_at = now() WHERE id = $1",
            empresa_id,
            empresa_estado,
        )

        if data.estado not in ("prueba", "activa"):
            await _revoke_sessions(conn, empresa_id)

    await _safe_audit(
        empresa_id=None,
        empresa_afectada_id=empresa_id,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="update",
        entidad="suscripcion",
        entidad_id=suscripcion_id,
        datos_antes=before,
        datos_despues={
            "plan_codigo": data.plan_codigo,
            "estado": data.estado,
            "fecha_inicio": str(data.fecha_inicio),
            "fecha_fin": str(data.fecha_fin),
            "renovacion_auto": data.renovacion_auto,
        },
        ip=ip,
        es_accion_superadmin=True,
        metodo="PUT",
        endpoint=f"/api/v1/saas/empresas/{empresa_id}/suscripcion",
        parametros={"plan_codigo": data.plan_codigo, "estado": data.estado},
    )

    return await get_empresa_suscripcion(empresa_id)


async def suspend_empresa(
    empresa_id: str,
    motivo: str | None,
    *,
    actor_id: str,
    ip: str | None,
) -> EstadoEmpresaResponse:
    async with admin_connection() as conn:
        empresa = await conn.fetchrow(
            """
            SELECT id, nombre, estado
              FROM empresa
             WHERE id = $1 AND deleted_at IS NULL
             FOR UPDATE
            """,
            empresa_id,
        )
        if empresa is None:
            raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
        if empresa["estado"] == "cancelada":
            raise api_error(409, "EMPRESA_CANCELADA", "La empresa esta cancelada")

        current = await conn.fetchrow(
            """
            SELECT id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
              FROM suscripcion
             WHERE empresa_id = $1
               AND estado <> 'cancelada'
             ORDER BY fecha_inicio DESC, created_at DESC
             LIMIT 1
             FOR UPDATE
            """,
            empresa_id,
        )
        if current is None:
            raise api_error(409, "SIN_SUSCRIPCION", "La empresa no tiene una suscripcion activa")

        before = _suscripcion_data(current)
        await conn.execute(
            "UPDATE suscripcion SET estado = 'suspendida', updated_at = now() WHERE id = $1",
            current["id"],
        )
        await conn.execute(
            "UPDATE empresa SET estado = 'suspendida', updated_at = now() WHERE id = $1",
            empresa_id,
        )
        await _revoke_sessions(conn, empresa_id)

    await _safe_audit(
        empresa_id=None,
        empresa_afectada_id=empresa_id,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="update",
        entidad="empresa",
        entidad_id=empresa_id,
        datos_antes=before,
        datos_despues={"estado": "suspendida", "motivo": motivo},
        ip=ip,
        es_accion_superadmin=True,
        metodo="POST",
        endpoint=f"/api/v1/saas/empresas/{empresa_id}/suspender",
        parametros={"motivo": motivo},
    )

    return EstadoEmpresaResponse(
        mensaje="Servicio suspendido y sesiones revocadas.",
        empresa_id=empresa_id,
        estado="suspendida",
        suscripcion_estado="suspendida",
    )


async def reactivate_empresa(
    empresa_id: str,
    motivo: str | None,
    *,
    actor_id: str,
    ip: str | None,
) -> EstadoEmpresaResponse:
    async with admin_connection() as conn:
        empresa = await conn.fetchrow(
            """
            SELECT id, nombre, estado
              FROM empresa
             WHERE id = $1 AND deleted_at IS NULL
             FOR UPDATE
            """,
            empresa_id,
        )
        if empresa is None:
            raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
        if empresa["estado"] == "cancelada":
            raise api_error(409, "EMPRESA_CANCELADA", "La empresa esta cancelada")

        current = await conn.fetchrow(
            """
            SELECT id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
              FROM suscripcion
             WHERE empresa_id = $1
               AND estado <> 'cancelada'
             ORDER BY fecha_inicio DESC, created_at DESC
             LIMIT 1
             FOR UPDATE
            """,
            empresa_id,
        )
        if current is None:
            raise api_error(409, "SIN_SUSCRIPCION", "La empresa no tiene una suscripcion registrada")
        if current["fecha_fin"] is not None and current["fecha_fin"] < date.today():
            raise api_error(
                409,
                "SUSCRIPCION_VENCIDA",
                "La suscripcion esta vencida. Asigne un nuevo periodo antes de reactivar.",
            )

        otra = await conn.fetchval(
            """
            SELECT 1
              FROM suscripcion
             WHERE empresa_id = $1
               AND id <> $2
               AND estado IN ('prueba', 'activa', 'mora')
             LIMIT 1
            """,
            empresa_id,
            current["id"],
        )
        if otra:
            raise api_error(
                409,
                "SUSCRIPCION_ACTIVA_EXISTENTE",
                "La empresa ya tiene otra suscripcion activa",
            )

        before = _suscripcion_data(current)
        await conn.execute(
            "UPDATE suscripcion SET estado = 'activa', updated_at = now() WHERE id = $1",
            current["id"],
        )
        await conn.execute(
            "UPDATE empresa SET estado = 'activa', updated_at = now() WHERE id = $1",
            empresa_id,
        )

    await _safe_audit(
        empresa_id=None,
        empresa_afectada_id=empresa_id,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="update",
        entidad="empresa",
        entidad_id=empresa_id,
        datos_antes=before,
        datos_despues={"estado": "activa", "motivo": motivo},
        ip=ip,
        es_accion_superadmin=True,
        metodo="POST",
        endpoint=f"/api/v1/saas/empresas/{empresa_id}/reactivar",
        parametros={"motivo": motivo},
    )

    return EstadoEmpresaResponse(
        mensaje="Servicio reactivado correctamente.",
        empresa_id=empresa_id,
        estado="activa",
        suscripcion_estado="activa",
    )


async def get_metricas() -> MetricasSaaSOut:
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                (SELECT count(*) FROM empresa WHERE deleted_at IS NULL) AS total_tenants,
                (
                    SELECT count(*)
                      FROM empresa
                     WHERE deleted_at IS NULL
                       AND estado = 'activa'
                ) AS empresas_activas,
                (
                    SELECT count(*)
                      FROM suscripcion s
                      JOIN empresa e ON e.id = s.empresa_id
                     WHERE e.deleted_at IS NULL
                       AND s.estado IN ('prueba', 'activa', 'mora')
                       AND s.fecha_fin IS NOT NULL
                       AND s.fecha_fin BETWEEN CURRENT_DATE AND CURRENT_DATE + 7
                ) AS suscripciones_por_vencer,
                (
                    SELECT COALESCE(sum(v.total), 0)
                      FROM venta v
                      JOIN empresa e ON e.id = v.empresa_id
                     WHERE e.deleted_at IS NULL
                       AND v.deleted_at IS NULL
                       AND v.estado = 'completada'
                       AND v.fecha_hora >= date_trunc('month', CURRENT_DATE)
                       AND v.fecha_hora < date_trunc('month', CURRENT_DATE) + interval '1 month'
                ) AS volumen_transaccional
            """
        )

    today = date.today()
    periodo_inicio = today.replace(day=1)
    if periodo_inicio.month == 12:
        next_month = periodo_inicio.replace(year=periodo_inicio.year + 1, month=1)
    else:
        next_month = periodo_inicio.replace(month=periodo_inicio.month + 1)

    return MetricasSaaSOut(
        total_tenants=int(row["total_tenants"] or 0),
        empresas_activas=int(row["empresas_activas"] or 0),
        suscripciones_por_vencer=int(row["suscripciones_por_vencer"] or 0),
        volumen_transaccional=Decimal(str(row["volumen_transaccional"] or 0)),
        periodo_inicio=periodo_inicio,
        periodo_fin=next_month - timedelta(days=1),
    )
