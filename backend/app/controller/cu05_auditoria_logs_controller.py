"""Controlador Backend para CU-05: Auditoría y Logs del Sistema."""

from datetime import date, datetime
import json
from typing import Any
from uuid import UUID

from asyncpg import Connection, Pool

from app.core.errors import api_error


def _parse_jsonb(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"valor": parsed}
        except Exception:
            return {"raw": value}
    return dict(value)


def _validate_uuid(value: str | None, field: str) -> UUID | None:
    if value is None or not str(value).strip():
        return None
    try:
        return UUID(str(value).strip())
    except ValueError as exc:
        raise api_error(422, "UUID_INVALIDO", f"El parametro '{field}' debe ser un UUID valido") from exc


def _row_to_item(row: Any) -> dict[str, Any]:
    ip_str = str(row["ip"]) if row["ip"] is not None else None
    ts = row["ocurrido_en"]
    entidad = str(row["entidad"])
    return {
        "id": int(row["id"]),
        "empresa_id": row["empresa_id"],
        "empresa_afectada_id": row["empresa_afectada_id"],
        "usuario_id": row["usuario_id"],
        "usuario_nombre": row["usuario_nombre"] if "usuario_nombre" in row.keys() else None,
        "usuario_correo": str(row["usuario_correo"]) if "usuario_correo" in row.keys() and row["usuario_correo"] is not None else None,
        "actor_tipo": str(row["actor_tipo"]),
        "accion": str(row["accion"]),
        "entidad": entidad,
        "modulo": entidad,
        "entidad_id": row["entidad_id"],
        "datos_antes": _parse_jsonb(row["datos_antes"]),
        "datos_despues": _parse_jsonb(row["datos_despues"]),
        "ip": ip_str,
        "ip_origen": ip_str,
        "ocurrido_en": ts,
        "fecha_hora": ts,
        "created_at": ts,
        "es_accion_superadmin": bool(row["es_accion_superadmin"]),
        "metodo": row["metodo"],
        "endpoint": row["endpoint"],
        "parametros": _parse_jsonb(row["parametros"]),
    }


class CU05AuditoriaLogsController:
    @staticmethod
    async def listar_logs_conn(
        conn: Connection,
        *,
        empresa_id: str | None = None,
        include_affected: bool = False,
        usuario_id: str | None = None,
        accion: str | None = None,
        entidad: str | None = None,
        fecha_inicio: date | datetime | None = None,
        fecha_fin: date | datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        conditions: list[str] = ["TRUE"]
        params: list[Any] = []

        empresa_uuid = _validate_uuid(empresa_id, "empresa_id")
        if empresa_uuid is not None:
            params.append(empresa_uuid)
            idx = len(params)
            if include_affected:
                conditions.append(f"(b.empresa_id = ${idx} OR b.empresa_afectada_id = ${idx})")
            else:
                conditions.append(f"b.empresa_id = ${idx}")

        usuario_uuid = _validate_uuid(usuario_id, "usuario_id")
        if usuario_uuid is not None:
            params.append(usuario_uuid)
            conditions.append(f"b.usuario_id = ${len(params)}")

        if accion and accion.strip():
            params.append(accion.strip().lower())
            conditions.append(f"lower(b.accion) = ${len(params)}")

        if entidad and entidad.strip():
            params.append(f"%{entidad.strip()}%")
            conditions.append(f"b.entidad ILIKE ${len(params)}")

        if fecha_inicio is not None:
            if isinstance(fecha_inicio, datetime):
                params.append(fecha_inicio)
                conditions.append(f"b.ocurrido_en >= ${len(params)}")
            else:
                params.append(fecha_inicio)
                conditions.append(f"b.ocurrido_en::date >= ${len(params)}")

        if fecha_fin is not None:
            if isinstance(fecha_fin, datetime):
                params.append(fecha_fin)
                conditions.append(f"b.ocurrido_en <= ${len(params)}")
            else:
                params.append(fecha_fin)
                conditions.append(f"b.ocurrido_en::date <= ${len(params)}")

        where_sql = " AND ".join(conditions)

        total = int(
            await conn.fetchval(
                f"SELECT count(*) FROM bitacora_auditoria b WHERE {where_sql}",
                *params,
            )
            or 0
        )

        offset = (page - 1) * page_size
        params.extend([page_size, offset])
        limit_idx = len(params) - 1
        offset_idx = len(params)

        rows = await conn.fetch(
            f"""
            SELECT b.id,
                   b.empresa_id,
                   b.empresa_afectada_id,
                   b.usuario_id,
                   u.nombre AS usuario_nombre,
                   u.correo AS usuario_correo,
                   b.actor_tipo,
                   b.accion,
                   b.entidad,
                   b.entidad_id,
                   b.datos_antes,
                   b.datos_despues,
                   host(b.ip) AS ip,
                   b.ocurrido_en,
                   b.es_accion_superadmin,
                   b.metodo,
                   b.endpoint,
                   b.parametros
              FROM bitacora_auditoria b
              LEFT JOIN usuario u ON u.id = b.usuario_id
             WHERE {where_sql}
             ORDER BY b.ocurrido_en DESC, b.id DESC
             LIMIT ${limit_idx} OFFSET ${offset_idx}
            """,
            *params,
        )

        return {
            "items": [_row_to_item(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def listar_logs(
        pool: Pool,
        empresa_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        page = (offset // max(1, limit)) + 1
        async with pool.acquire() as conn:
            res = await CU05AuditoriaLogsController.listar_logs_conn(
                conn,
                empresa_id=empresa_id,
                page=page,
                page_size=limit,
            )
            return res["items"]
