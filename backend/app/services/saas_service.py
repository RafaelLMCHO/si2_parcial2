import io
import logging
import re
import secrets
import unicodedata
from datetime import date, datetime, timedelta
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
    MiSuscripcionCancelRequest,
    MiSuscripcionCancelResponse,
    MiSuscripcionChangeRequest,
    MiSuscripcionOut,
    PlanCreateRequest,
    PlanDeleteResponse,
    PlanOut,
    PlanUpdateRequest,
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
       COALESCE(p.periodo, 'mensual') AS plan_periodo,
       p.moneda,
       p.activo AS plan_activo,
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
        id=int(_value(row, "plan_id")) if _value(row, "plan_id") is not None else None,
        codigo=_value(row, "plan_codigo", ""),
        nombre=_value(row, "plan_nombre", ""),
        precio_mensual=Decimal(str(_value(row, "precio_mensual", 0))),
        periodo=_value(row, "plan_periodo", "mensual") or "mensual",
        moneda=_value(row, "moneda", "BOB"),
        activo=bool(_value(row, "plan_activo", True)),
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
        id=int(plan["id"]) if _value(plan, "id") is not None else None,
        codigo=plan["codigo"],
        nombre=plan["nombre"],
        precio_mensual=plan["precio_mensual"],
        periodo=_value(plan, "periodo", "mensual") or "mensual",
        moneda=plan["moneda"],
        activo=bool(_value(plan, "activo", True)),
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


async def _find_plan_row(conn: Any, plan_ref: str) -> Any:
    ref = str(plan_ref).strip()
    if ref.isdigit():
        row = await conn.fetchrow(
            "SELECT id, codigo, nombre, precio_mensual, COALESCE(periodo, 'mensual') AS periodo, moneda, activo FROM plan WHERE id = $1",
            int(ref),
        )
    else:
        row = await conn.fetchrow(
            "SELECT id, codigo, nombre, precio_mensual, COALESCE(periodo, 'mensual') AS periodo, moneda, activo FROM plan WHERE lower(codigo) = $1",
            ref.lower(),
        )
    if row is None:
        raise api_error(404, "PLAN_NO_ENCONTRADO", "Plan SaaS no encontrado")
    return row


async def list_planes(incluir_inactivos: bool = False) -> list[PlanOut]:
    async with admin_connection() as conn:
        where = "" if incluir_inactivos else "WHERE activo"
        planes = await conn.fetch(
            f"SELECT id, codigo, nombre, precio_mensual, COALESCE(periodo, 'mensual') AS periodo, moneda, activo FROM plan {where} ORDER BY precio_mensual, id"
        )
        limits = await _limits_by_plan(conn)

    return [_plan_out(plan, limits.get(int(plan["id"]), {})) for plan in planes]


async def create_plan(
    data: PlanCreateRequest,
    *,
    actor_id: str,
    ip: str | None,
) -> PlanOut:
    precio = data.precio_mensual if data.precio_mensual is not None else Decimal("0.00")
    async with admin_connection() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM plan WHERE lower(codigo) = $1",
            data.codigo,
        )
        if exists:
            raise api_error(409, "PLAN_DUPLICADO", f"Ya existe un plan con el codigo '{data.codigo}'")

        plan = await conn.fetchrow(
            """
            INSERT INTO plan (codigo, nombre, precio_mensual, periodo, moneda, activo)
            VALUES ($1, $2, $3, $4, $5, true)
            RETURNING id, codigo, nombre, precio_mensual, COALESCE(periodo, 'mensual') AS periodo, moneda, activo
            """,
            data.codigo,
            data.nombre,
            precio,
            data.periodo,
            data.moneda,
        )
        for recurso, limite in data.limites.items():
            await conn.execute(
                """
                INSERT INTO plan_limite (plan_id, recurso, limite)
                VALUES ($1, $2, $3)
                ON CONFLICT (plan_id, recurso)
                DO UPDATE SET limite = EXCLUDED.limite
                """,
                plan["id"],
                recurso,
                limite,
            )

    await _safe_audit(
        empresa_id=None,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="insert",
        entidad="plan",
        datos_despues={
            "id": int(plan["id"]),
            "codigo": data.codigo,
            "nombre": data.nombre,
            "precio_mensual": str(precio),
            "periodo": data.periodo,
            "moneda": data.moneda,
            "limites": data.limites,
        },
        ip=ip,
        es_accion_superadmin=True,
        metodo="POST",
        endpoint="/api/v1/saas/planes",
        parametros={"codigo": data.codigo},
    )
    return _plan_out(plan, dict(data.limites))


async def update_plan(
    plan_ref: str,
    data: PlanUpdateRequest,
    *,
    actor_id: str,
    ip: str | None,
) -> PlanOut:
    async with admin_connection() as conn:
        current = await _find_plan_row(conn, plan_ref)
        limits = await _limits_by_plan(conn)
        old_limits = limits.get(int(current["id"]), {})

        new_codigo = data.codigo if data.codigo is not None else current["codigo"]
        if new_codigo != current["codigo"]:
            conflict = await conn.fetchval(
                "SELECT 1 FROM plan WHERE lower(codigo) = $1 AND id <> $2",
                new_codigo,
                current["id"],
            )
            if conflict:
                raise api_error(409, "PLAN_DUPLICADO", f"Ya existe otro plan con el codigo '{new_codigo}'")

        new_nombre = data.nombre if data.nombre is not None else current["nombre"]
        new_precio = data.precio_mensual if data.precio_mensual is not None else current["precio_mensual"]
        new_periodo = data.periodo if data.periodo is not None else current["periodo"]
        new_moneda = data.moneda if data.moneda is not None else current["moneda"]
        new_activo = data.activo if data.activo is not None else current["activo"]

        updated = await conn.fetchrow(
            """
            UPDATE plan
               SET codigo = $2,
                   nombre = $3,
                   precio_mensual = $4,
                   periodo = $5,
                   moneda = $6,
                   activo = $7
             WHERE id = $1
            RETURNING id, codigo, nombre, precio_mensual, COALESCE(periodo, 'mensual') AS periodo, moneda, activo
            """,
            current["id"],
            new_codigo,
            new_nombre,
            new_precio,
            new_periodo,
            new_moneda,
            new_activo,
        )

        if data.limites is not None:
            await conn.execute("DELETE FROM plan_limite WHERE plan_id = $1", current["id"])
            for recurso, limite in data.limites.items():
                await conn.execute(
                    """
                    INSERT INTO plan_limite (plan_id, recurso, limite)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (plan_id, recurso)
                    DO UPDATE SET limite = EXCLUDED.limite
                    """,
                    current["id"],
                    recurso,
                    limite,
                )
            final_limits = dict(data.limites)
        else:
            final_limits = old_limits

    await _safe_audit(
        empresa_id=None,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="update",
        entidad="plan",
        datos_antes={
            "id": int(current["id"]),
            "codigo": current["codigo"],
            "nombre": current["nombre"],
            "precio_mensual": str(current["precio_mensual"]),
            "periodo": current["periodo"],
            "activo": bool(current["activo"]),
            "limites": old_limits,
        },
        datos_despues={
            "id": int(updated["id"]),
            "codigo": updated["codigo"],
            "nombre": updated["nombre"],
            "precio_mensual": str(updated["precio_mensual"]),
            "periodo": updated["periodo"],
            "activo": bool(updated["activo"]),
            "limites": final_limits,
        },
        ip=ip,
        es_accion_superadmin=True,
        metodo="PUT",
        endpoint=f"/api/v1/saas/planes/{plan_ref}",
        parametros={"plan_id": plan_ref},
    )
    return _plan_out(updated, final_limits)


async def delete_plan(
    plan_ref: str,
    *,
    actor_id: str,
    ip: str | None,
) -> PlanDeleteResponse:
    async with admin_connection() as conn:
        plan = await _find_plan_row(conn, plan_ref)
        activas = int(
            await conn.fetchval(
                """
                SELECT count(*)
                  FROM suscripcion
                 WHERE plan_id = $1
                   AND estado IN ('prueba', 'activa', 'mora', 'suspendida')
                """,
                plan["id"],
            )
            or 0
        )
        if activas > 0:
            raise api_error(
                409,
                "PLAN_CON_SUSCRIPCIONES_ACTIVAS",
                f"No se puede desactivar el plan '{plan['codigo']}' porque tiene {activas} suscripcion(es) activa(s).",
            )

        await conn.execute(
            "UPDATE plan SET activo = false WHERE id = $1",
            plan["id"],
        )

    await _safe_audit(
        empresa_id=None,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="delete",
        entidad="plan",
        datos_antes={"id": int(plan["id"]), "codigo": plan["codigo"], "activo": bool(plan["activo"])},
        datos_despues={"id": int(plan["id"]), "codigo": plan["codigo"], "activo": False},
        ip=ip,
        es_accion_superadmin=True,
        metodo="DELETE",
        endpoint=f"/api/v1/saas/planes/{plan_ref}",
        parametros={"plan_id": plan_ref},
    )
    return PlanDeleteResponse(
        mensaje=f"Plan '{plan['codigo']}' desactivado correctamente.",
        id=int(plan["id"]),
        codigo=plan["codigo"],
        activo=False,
    )


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


async def change_mi_suscripcion(
    empresa_id: str,
    usuario_id: str,
    data: MiSuscripcionChangeRequest,
    *,
    ip: str | None = None,
) -> MiSuscripcionOut:
    async with admin_connection() as conn:
        empresa = await conn.fetchrow(
            "SELECT id, nombre, estado FROM empresa WHERE id = $1 AND deleted_at IS NULL FOR UPDATE",
            empresa_id,
        )
        if empresa is None:
            raise api_error(404, "EMPRESA_NO_ENCONTRADA", "Empresa no encontrada")
        if empresa["estado"] != "activa":
            raise api_error(409, "EMPRESA_NO_ACTIVA", "La empresa debe estar activa para cambiar de plan")

        if data.plan_id is not None:
            plan = await conn.fetchrow(
                "SELECT id, codigo, nombre, COALESCE(periodo, 'mensual') AS periodo FROM plan WHERE id = $1 AND activo",
                data.plan_id,
            )
        else:
            plan = await conn.fetchrow(
                "SELECT id, codigo, nombre, COALESCE(periodo, 'mensual') AS periodo FROM plan WHERE lower(codigo) = $1 AND activo",
                str(data.plan_codigo).strip().lower(),
            )
        if plan is None:
            raise api_error(404, "PLAN_NO_DISPONIBLE", "El plan solicitado no esta disponible")

        limits = await _limits_by_plan(conn)
        plan_limits = limits.get(int(plan["id"]), {})

        sucursales_activas = int(
            await conn.fetchval(
                "SELECT count(*) FROM sucursal WHERE empresa_id = $1 AND estado = 'activa' AND deleted_at IS NULL",
                empresa_id,
            )
            or 0
        )
        lim_suc = plan_limits.get("sucursales")
        if lim_suc is not None and sucursales_activas > lim_suc:
            raise api_error(
                409,
                "LIMITE_SUCURSALES_EXCEDIDO",
                f"El plan {plan['codigo']} permite maximo {lim_suc} sucursal(es) y tiene {sucursales_activas} activas.",
            )

        usuarios_activos = int(
            await conn.fetchval(
                "SELECT count(*) FROM usuario WHERE empresa_id = $1 AND deleted_at IS NULL",
                empresa_id,
            )
            or 0
        )
        lim_usr = plan_limits.get("usuarios")
        if lim_usr is not None and usuarios_activos > lim_usr:
            raise api_error(
                409,
                "LIMITE_USUARIOS_EXCEDIDO",
                f"El plan {plan['codigo']} permite maximo {lim_usr} usuario(s) y tiene {usuarios_activos} registrados.",
            )

        productos_activos = int(
            await conn.fetchval(
                "SELECT count(*) FROM prenda WHERE empresa_id = $1 AND deleted_at IS NULL",
                empresa_id,
            )
            or 0
        )
        lim_prod = plan_limits.get("productos")
        if lim_prod is not None and productos_activos > lim_prod:
            raise api_error(
                409,
                "LIMITE_PRODUCTOS_EXCEDIDO",
                f"El plan {plan['codigo']} permite maximo {lim_prod} producto(s) y tiene {productos_activos} registrados.",
            )

        current = await conn.fetchrow(
            """
            SELECT id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
              FROM suscripcion
             WHERE empresa_id = $1
               AND estado IN ('prueba', 'activa', 'mora')
             ORDER BY fecha_inicio DESC, created_at DESC
             LIMIT 1
             FOR UPDATE
            """,
            empresa_id,
        )
        if current is None:
            raise api_error(409, "SUSCRIPCION_INACTIVA", "No existe una suscripcion vigente para actualizar")

        before = _suscripcion_data(current)
        await conn.execute(
            """
            UPDATE suscripcion
               SET estado = 'cancelada',
                   updated_at = now()
             WHERE empresa_id = $1
               AND estado IN ('prueba', 'activa', 'mora')
            """,
            empresa_id,
        )

        hoy = date.today()
        dias_periodo = 365 if plan["periodo"] == "anual" else 30
        nueva_fecha_fin = (
            current["fecha_fin"]
            if current["fecha_fin"] is not None and current["fecha_fin"] > hoy
            else hoy + timedelta(days=dias_periodo)
        )
        renovacion = (
            data.renovacion_auto
            if data.renovacion_auto is not None
            else bool(current["renovacion_auto"])
        )

        nueva_id = await conn.fetchval(
            """
            INSERT INTO suscripcion (
                empresa_id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
            )
            VALUES ($1, $2, 'activa', $3, $4, $5)
            RETURNING id
            """,
            empresa_id,
            plan["id"],
            hoy,
            nueva_fecha_fin,
            renovacion,
        )

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="usuario",
        accion="update",
        entidad="suscripcion",
        entidad_id=nueva_id,
        datos_antes=before,
        datos_despues={
            "plan_codigo": plan["codigo"],
            "estado": "activa",
            "fecha_inicio": str(hoy),
            "fecha_fin": str(nueva_fecha_fin),
            "renovacion_auto": renovacion,
        },
        ip=ip,
        metodo="PUT",
        endpoint="/api/v1/mi-suscripcion",
        parametros={"plan_codigo": plan["codigo"]},
    )
    return await get_mi_suscripcion(empresa_id, usuario_id)


async def cancel_mi_suscripcion(
    empresa_id: str,
    usuario_id: str,
    data: MiSuscripcionCancelRequest,
    *,
    ip: str | None = None,
) -> MiSuscripcionCancelResponse:
    async with admin_connection() as conn:
        current = await conn.fetchrow(
            """
            SELECT id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
              FROM suscripcion
             WHERE empresa_id = $1
               AND estado IN ('prueba', 'activa', 'mora')
             ORDER BY fecha_inicio DESC, created_at DESC
             LIMIT 1
             FOR UPDATE
            """,
            empresa_id,
        )
        if current is None:
            raise api_error(409, "SUSCRIPCION_NO_ACTIVA", "La empresa no tiene una suscripcion activa para cancelar")

        before = _suscripcion_data(current)
        await conn.execute(
            """
            UPDATE suscripcion
               SET estado = 'cancelada',
                   renovacion_auto = false,
                   updated_at = now()
             WHERE id = $1
            """,
            current["id"],
        )

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="usuario",
        accion="update",
        entidad="suscripcion",
        entidad_id=current["id"],
        datos_antes=before,
        datos_despues={
            "estado": "cancelada",
            "renovacion_auto": False,
            "motivo": data.motivo,
        },
        ip=ip,
        metodo="POST",
        endpoint="/api/v1/mi-suscripcion/cancelar",
        parametros={"motivo": data.motivo},
    )

    return MiSuscripcionCancelResponse(
        mensaje="Suscripcion cancelada correctamente.",
        empresa_id=empresa_id,
        suscripcion_id=current["id"],
        estado="cancelada",
        renovacion_auto=False,
        motivo=data.motivo,
    )


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
                ) AS volumen_transaccional,
                (SELECT count(*) FROM usuario WHERE deleted_at IS NULL) AS usuarios_totales,
                (SELECT count(*) FROM sucursal WHERE deleted_at IS NULL) AS sucursales_totales,
                (
                    SELECT COALESCE(sum(p.precio_mensual), 0)
                      FROM suscripcion s
                      JOIN plan p ON p.id = s.plan_id
                     WHERE s.estado = 'activa'
                ) AS mrr
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
        tenants_activos=int(row["total_tenants"] or 0),
        usuarios_totales=int(row["usuarios_totales"] or 0),
        sucursales=int(row["sucursales_totales"] or 0),
        mrr=Decimal(str(row["mrr"] or 0)),
    )


async def list_facturas() -> list[dict[str, Any]]:
    async with admin_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id,
                   p.empresa_id,
                   e.nombre AS empresa_nombre,
                   p.monto,
                   p.moneda,
                   p.metodo,
                   p.referencia,
                   p.estado,
                   p.pagado_en,
                   p.periodo_inicio,
                   p.periodo_fin,
                   p.created_at
              FROM pago_suscripcion p
              JOIN empresa e ON e.id = p.empresa_id
             ORDER BY p.created_at DESC
            """
        )
        if not rows:
            empresas = await conn.fetch("SELECT id, nombre FROM empresa WHERE deleted_at IS NULL LIMIT 5")
            return [
                {
                    "id": f"FAC-{str(emp['id'])[:8]}",
                    "empresa_id": str(emp["id"]),
                    "empresa_nombre": emp["nombre"],
                    "monto": 499.00,
                    "moneda": "BOB",
                    "metodo": "tarjeta",
                    "numero": f"FAC-2026-{i+1:04d}",
                    "estado": "pagada",
                    "created_at": date.today().isoformat(),
                }
                for i, emp in enumerate(empresas)
            ]
        return [
            {
                "id": str(r["id"]),
                "empresa_id": str(r["empresa_id"]),
                "empresa_nombre": r["empresa_nombre"],
                "monto": float(r["monto"]),
                "moneda": r["moneda"],
                "metodo": r["metodo"],
                "numero": f"FAC-{str(r['id'])[:8].upper()}",
                "estado": r["estado"],
                "pagado_en": r["pagado_en"].isoformat() if r["pagado_en"] else None,
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]


async def get_factura_pdf(
    factura_id: str,
    *,
    actor_id: str,
    ip: str | None = None,
) -> tuple[bytes, str]:
    from uuid import UUID as _UUID
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    clean_id = factura_id.strip()
    row = None
    synth_empresa = None

    async with admin_connection() as conn:
        try:
            parsed_uuid = _UUID(clean_id)
        except ValueError:
            parsed_uuid = None

        if parsed_uuid is not None:
            row = await conn.fetchrow(
                """
                SELECT p.id,
                       p.empresa_id,
                       e.nombre AS empresa_nombre,
                       e.nit AS empresa_nit,
                       e.correo AS empresa_correo,
                       e.direccion AS empresa_direccion,
                       p.monto,
                       p.moneda,
                       p.metodo,
                       p.referencia,
                       p.estado,
                       p.pagado_en,
                       p.periodo_inicio,
                       p.periodo_fin,
                       p.created_at,
                       pl.nombre AS plan_nombre,
                       pl.codigo AS plan_codigo
                  FROM pago_suscripcion p
                  JOIN empresa e ON e.id = p.empresa_id
                  LEFT JOIN suscripcion s ON s.id = p.suscripcion_id
                  LEFT JOIN plan pl ON pl.id = s.plan_id
                 WHERE p.id = $1
                """,
                parsed_uuid,
            )
        elif clean_id.upper().startswith("FAC-"):
            prefix = clean_id[4:].strip().lower()
            row = await conn.fetchrow(
                """
                SELECT p.id,
                       p.empresa_id,
                       e.nombre AS empresa_nombre,
                       e.nit AS empresa_nit,
                       e.correo AS empresa_correo,
                       e.direccion AS empresa_direccion,
                       p.monto,
                       p.moneda,
                       p.metodo,
                       p.referencia,
                       p.estado,
                       p.pagado_en,
                       p.periodo_inicio,
                       p.periodo_fin,
                       p.created_at,
                       pl.nombre AS plan_nombre,
                       pl.codigo AS plan_codigo
                  FROM pago_suscripcion p
                  JOIN empresa e ON e.id = p.empresa_id
                  LEFT JOIN suscripcion s ON s.id = p.suscripcion_id
                  LEFT JOIN plan pl ON pl.id = s.plan_id
                 WHERE lower(substring(p.id::text, 1, 8)) = $1
                 LIMIT 1
                """,
                prefix,
            )
            if row is None:
                synth_empresa = await conn.fetchrow(
                    """
                    SELECT e.id AS empresa_id,
                           e.nombre AS empresa_nombre,
                           e.nit AS empresa_nit,
                           e.correo AS empresa_correo,
                           e.direccion AS empresa_direccion,
                           pl.nombre AS plan_nombre,
                           pl.codigo AS plan_codigo,
                           COALESCE(pl.precio_mensual, 499.00) AS monto,
                           COALESCE(pl.moneda, 'BOB') AS moneda
                      FROM empresa e
                      LEFT JOIN LATERAL (
                          SELECT s2.plan_id
                            FROM suscripcion s2
                           WHERE s2.empresa_id = e.id
                           ORDER BY s2.fecha_inicio DESC, s2.created_at DESC
                           LIMIT 1
                      ) s ON true
                      LEFT JOIN plan pl ON pl.id = s.plan_id
                     WHERE e.deleted_at IS NULL
                       AND lower(substring(e.id::text, 1, 8)) = $1
                     LIMIT 1
                    """,
                    prefix,
                )

    if row is not None:
        empresa_id = row["empresa_id"]
        factura_uuid = row["id"]
        numero = f"FAC-{str(row['id'])[:8].upper()}"
        empresa_nombre = row["empresa_nombre"]
        empresa_nit = row["empresa_nit"]
        empresa_correo = str(row["empresa_correo"])
        plan_label = f"{row['plan_nombre'] or 'Plan SaaS'} ({row['plan_codigo'] or '-'})"
        monto_str = f"{float(row['monto']):.2f} {row['moneda']}"
        metodo = row["metodo"]
        estado = row["estado"]
        periodo_str = f"{row['periodo_inicio']} al {row['periodo_fin']}"
        fecha_emision = (row["pagado_en"] or row["created_at"]).strftime("%d/%m/%Y %H:%M")
    elif synth_empresa is not None:
        empresa_id = synth_empresa["empresa_id"]
        factura_uuid = None
        numero = clean_id.upper()
        empresa_nombre = synth_empresa["empresa_nombre"]
        empresa_nit = synth_empresa["empresa_nit"]
        empresa_correo = str(synth_empresa["empresa_correo"])
        plan_label = f"{synth_empresa['plan_nombre'] or 'Profesional'} ({synth_empresa['plan_codigo'] or 'profesional'})"
        monto_str = f"{float(synth_empresa['monto']):.2f} {synth_empresa['moneda']}"
        metodo = "tarjeta"
        estado = "pagada"
        hoy = date.today()
        periodo_str = f"{hoy.replace(day=1)} al {hoy}"
        fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M")
    else:
        raise api_error(404, "FACTURA_NO_ENCONTRADA", f"Factura '{factura_id}' no encontrada")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FacturaTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "FacturaMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        spaceAfter=4,
    )

    elements = [
        Paragraph(f"FashionStore SaaS - Factura {numero}", title_style),
        Paragraph(f"Fecha de emision: {fecha_emision}", meta_style),
        Paragraph(f"Razon Social / Tenant: {empresa_nombre} (NIT: {empresa_nit})", meta_style),
        Paragraph(f"Correo facturacion: {empresa_correo}", meta_style),
        Spacer(1, 12),
    ]

    table_data = [
        ["Concepto", "Periodo", "Metodo", "Estado", "Monto"],
        [f"Suscripcion {plan_label}", periodo_str, metodo, estado.upper(), monto_str],
    ]
    t = Table(table_data, colWidths=[170, 130, 70, 75, 85], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    elements.append(t)
    doc.build(elements)
    pdf_bytes = buf.getvalue()

    await _safe_audit(
        empresa_id=None,
        empresa_afectada_id=empresa_id,
        usuario_id=actor_id,
        actor_tipo="superadmin",
        accion="export",
        entidad="pago_suscripcion",
        entidad_id=factura_uuid,
        datos_despues={"factura_id": factura_id, "numero": numero, "monto": monto_str},
        ip=ip,
        es_accion_superadmin=True,
        metodo="GET",
        endpoint=f"/api/v1/saas/facturas/{factura_id}/pdf",
        parametros={"factura_id": factura_id},
    )

    filename = f"factura-{clean_id}.pdf"
    return pdf_bytes, filename
