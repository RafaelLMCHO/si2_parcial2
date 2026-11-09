import asyncio
import hashlib
import json
import logging
import os
import shutil
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.api.deps import CurrentUser
from app.core.errors import api_error
from app.db import audit_event, get_pool
from app.schemas.backup import (
    BackupConfiguracionOut,
    BackupConfiguracionUpdate,
    BackupEstadisticasOut,
    BackupListResponse,
    BackupManualCreate,
    BackupModuloInfo,
    BackupRegistroOut,
    BackupRestaurarRequest,
)

logger = logging.getLogger("backup_service")

# Directorios de almacenamiento para Localhost y Nube
BASE_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "backups"
LOCAL_STORAGE_DIR = BASE_STORAGE_DIR / "local"
CLOUD_STORAGE_DIR = BASE_STORAGE_DIR / "cloud"

LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CLOUD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CLOUD_PROVIDER_NAME = "AWS S3 (sa-east-1)"
CLOUD_BUCKET_NAME = "fashionstore-backups"

# Definición de Módulos Funcionales y sus tablas
MODULOS_CATALOGO: dict[str, BackupModuloInfo] = {
    "catalogo": BackupModuloInfo(
        id="catalogo",
        nombre="Catálogo de Productos",
        descripcion="Categorías, temporadas, colecciones, colores, tallas, prendas, variantes y precios",
        tablas=[
            "categoria",
            "temporada",
            "coleccion",
            "color",
            "talla",
            "prenda",
            "variante",
            "prenda_recurso",
            "prenda_ar",
            "precio_historial",
        ],
    ),
    "inventario": BackupModuloInfo(
        id="inventario",
        nombre="Inventario & Sucursales",
        descripcion="Proveedores, sucursales, existencias de inventario y transferencias",
        tablas=[
            "proveedor",
            "sucursal",
            "inventario",
            "transferencia_inventario",
            "transferencia_detalle",
        ],
    ),
    "ventas": BackupModuloInfo(
        id="ventas",
        nombre="Ventas & Facturación POS",
        descripcion="Ventas realizadas, detalles de venta, pagos, cupones y cambios de prendas",
        tablas=[
            "venta",
            "venta_detalle",
            "venta_estado_historial",
            "pago",
            "cupon",
            "cupon_uso",
            "cambio_prenda",
            "cambio_detalle",
            "nota_cambio",
        ],
    ),
    "clientes": BackupModuloInfo(
        id="clientes",
        nombre="Clientes & Carritos",
        descripcion="Información de clientes, direcciones, carritos activos y segmentos",
        tablas=[
            "cliente",
            "direccion_cliente",
            "segmento_cliente",
            "carrito",
            "carrito_detalle",
        ],
    ),
    "reservas": BackupModuloInfo(
        id="reservas",
        nombre="Reservas & Probador Virtual",
        descripcion="Reservas de probadores, detalles, bloqueos temporales (soft-lock) y sesiones",
        tablas=[
            "reserva",
            "reserva_detalle",
            "reserva_estado_historial",
            "soft_lock",
            "sesion_prueba_virtual",
        ],
    ),
    "usuarios": BackupModuloInfo(
        id="usuarios",
        nombre="Usuarios & Seguridad",
        descripcion="Cuentas de usuario de la empresa, roles y asignación de permisos",
        tablas=[
            "usuario",
            "rol",
            "rol_permiso",
        ],
    ),
    "offline": BackupModuloInfo(
        id="offline",
        nombre="Operaciones Offline & Sincronización",
        descripcion="Cola de operaciones pendientes, resolución de conflictos y registros de sincronización",
        tablas=[
            "operacion_pendiente",
            "resolucion_conflicto",
            "sync_registro_idempotencia",
        ],
    ),
    "auditoria": BackupModuloInfo(
        id="auditoria",
        nombre="Bitácora de Auditoría",
        descripcion="Registro de auditoría del sistema, consultas y reportes generados",
        tablas=[
            "bitacora_auditoria",
            "reporte_exportado",
            "consulta_ia_log",
        ],
    ),
}

MODULO_SAAS_GLOBAL = BackupModuloInfo(
    id="saas_global",
    nombre="SaaS Plataforma Global",
    descripcion="Planes SaaS, suscripciones de empresas, cobros y facturación global",
    tablas=[
        "empresa",
        "plan",
        "plan_limite",
        "suscripcion",
        "pago_suscripcion",
        "stripe_evento",
    ],
)


def _custom_json_serializer(obj: Any) -> Any:
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.hex()
    raise TypeError(f"Objeto no serializable: {type(obj)} - {obj}")


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _calculate_next_run(
    frecuencia: str,
    hora_str: str = "02:00",
    dia_semana: int = 0,
    dia_mes: int = 1,
    fecha_inicio: date | None = None,
    fecha_especifica: date | None = None,
    from_time: datetime | None = None,
) -> datetime:
    now = from_time or datetime.now(timezone.utc)
    try:
        parts = hora_str.split(":")
        target_h = int(parts[0])
        target_m = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        target_h, target_m = 2, 0

    base_date = now.date()
    if fecha_inicio and fecha_inicio > base_date:
        base_date = fecha_inicio

    if frecuencia == "fecha_especifica":
        target_date = fecha_especifica or base_date
        return datetime(
            target_date.year, target_date.month, target_date.day,
            target_h, target_m, 0, tzinfo=timezone.utc
        )

    if frecuencia == "cada_hora":
        return now + timedelta(hours=1)
    elif frecuencia == "cada_2_horas":
        return now + timedelta(hours=2)
    elif frecuencia == "cada_4_horas":
        return now + timedelta(hours=4)
    elif frecuencia == "cada_6_horas":
        return now + timedelta(hours=6)
    elif frecuencia == "cada_12_horas":
        return now + timedelta(hours=12)
    elif frecuencia == "diario":
        candidate = datetime(
            base_date.year, base_date.month, base_date.day,
            target_h, target_m, 0, tzinfo=timezone.utc
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate
    elif frecuencia == "semanal":
        candidate = datetime(
            base_date.year, base_date.month, base_date.day,
            target_h, target_m, 0, tzinfo=timezone.utc
        )
        days_ahead = dia_semana - candidate.weekday()
        if days_ahead < 0 or (days_ahead == 0 and candidate <= now):
            days_ahead += 7
        return candidate + timedelta(days=days_ahead)
    elif frecuencia == "mensual":
        target_day = max(1, min(dia_mes, 28))
        candidate = datetime(
            base_date.year, base_date.month, target_day,
            target_h, target_m, 0, tzinfo=timezone.utc
        )
        if candidate <= now:
            year = candidate.year + (1 if candidate.month == 12 else 0)
            month = 1 if candidate.month == 12 else candidate.month + 1
            candidate = datetime(year, month, target_day, target_h, target_m, 0, tzinfo=timezone.utc)
        return candidate

    return now + timedelta(days=1)


class BackupService:
    @staticmethod
    def get_available_modules(is_superadmin: bool = False) -> list[BackupModuloInfo]:
        modules = list(MODULOS_CATALOGO.values())
        if is_superadmin:
            modules.append(MODULO_SAAS_GLOBAL)
        return modules

    @staticmethod
    async def get_configuracion(empresa_id: str | None) -> BackupConfiguracionOut:
        pool = get_pool()
        async with pool.acquire() as conn:
            if empresa_id:
                row = await conn.fetchrow(
                    """
                    SELECT id, empresa_id, activo, frecuencia, fecha_inicio, fecha_especifica,
                           hora_ejecucion, dia_semana, dia_mes, destino, formato, tablas,
                           retencion_dias, ultima_ejecucion, proxima_ejecucion,
                           estado_ultima_ejecucion, error_ultima_ejecucion, updated_at
                    FROM backup_configuracion
                    WHERE empresa_id = $1
                    """,
                    UUID(empresa_id),
                )
            else:
                row = await conn.fetchrow(
                    """
                    SELECT id, empresa_id, activo, frecuencia, fecha_inicio, fecha_especifica,
                           hora_ejecucion, dia_semana, dia_mes, destino, formato, tablas,
                           retencion_dias, ultima_ejecucion, proxima_ejecucion,
                           estado_ultima_ejecucion, error_ultima_ejecucion, updated_at
                    FROM backup_configuracion
                    WHERE empresa_id IS NULL
                    """
                )

            if row:
                tablas_list = row["tablas"]
                if isinstance(tablas_list, str):
                    tablas_list = json.loads(tablas_list)
                return BackupConfiguracionOut(
                    id=str(row["id"]),
                    empresa_id=str(row["empresa_id"]) if row["empresa_id"] else None,
                    activo=row["activo"],
                    frecuencia=row["frecuencia"],
                    fecha_inicio=row["fecha_inicio"],
                    fecha_especifica=row["fecha_especifica"],
                    hora_ejecucion=row["hora_ejecucion"],
                    dia_semana=row["dia_semana"],
                    dia_mes=row["dia_mes"] or 1,
                    destino=row["destino"],
                    formato=row["formato"],
                    tablas=tablas_list or ["catalogo", "inventario", "ventas"],
                    retencion_dias=row["retencion_dias"],
                    ultima_ejecucion=row["ultima_ejecucion"],
                    proxima_ejecucion=row["proxima_ejecucion"],
                    estado_ultima_ejecucion=row["estado_ultima_ejecucion"],
                    error_ultima_ejecucion=row["error_ultima_ejecucion"],
                    updated_at=row["updated_at"],
                )

            # Si no existe, crear una configuración por defecto
            proxima = _calculate_next_run("diario", "02:00")
            default_tablas = json.dumps(["catalogo", "inventario", "ventas", "reservas", "clientes"])
            if empresa_id:
                new_row = await conn.fetchrow(
                    """
                    INSERT INTO backup_configuracion (
                        empresa_id, activo, frecuencia, hora_ejecucion, dia_semana, dia_mes,
                        destino, formato, tablas, retencion_dias, proxima_ejecucion
                    ) VALUES ($1, false, 'diario', '02:00', 0, 1, 'ambos', 'json', $2::jsonb, 30, $3)
                    RETURNING *
                    """,
                    UUID(empresa_id),
                    default_tablas,
                    proxima,
                )
            else:
                new_row = await conn.fetchrow(
                    """
                    INSERT INTO backup_configuracion (
                        empresa_id, activo, frecuencia, hora_ejecucion, dia_semana, dia_mes,
                        destino, formato, tablas, retencion_dias, proxima_ejecucion
                    ) VALUES (NULL, false, 'diario', '02:00', 0, 1, 'ambos', 'json', $1::jsonb, 30, $2)
                    RETURNING *
                    """,
                    default_tablas,
                    proxima,
                )

            return BackupConfiguracionOut(
                id=str(new_row["id"]),
                empresa_id=str(new_row["empresa_id"]) if new_row["empresa_id"] else None,
                activo=new_row["activo"],
                frecuencia=new_row["frecuencia"],
                fecha_inicio=new_row["fecha_inicio"],
                fecha_especifica=new_row["fecha_especifica"],
                hora_ejecucion=new_row["hora_ejecucion"],
                dia_semana=new_row["dia_semana"],
                dia_mes=new_row["dia_mes"] or 1,
                destino=new_row["destino"],
                formato=new_row["formato"],
                tablas=json.loads(default_tablas),
                retencion_dias=new_row["retencion_dias"],
                ultima_ejecucion=None,
                proxima_ejecucion=new_row["proxima_ejecucion"],
                estado_ultima_ejecucion=None,
                error_ultima_ejecucion=None,
                updated_at=new_row["updated_at"],
            )

    @staticmethod
    async def update_configuracion(
        empresa_id: str | None,
        data: BackupConfiguracionUpdate,
        current_user: CurrentUser | None = None,
    ) -> BackupConfiguracionOut:
        pool = get_pool()
        proxima = _calculate_next_run(
            frecuencia=data.frecuencia,
            hora_str=data.hora_ejecucion,
            dia_semana=data.dia_semana,
            dia_mes=data.dia_mes,
            fecha_inicio=data.fecha_inicio,
            fecha_especifica=data.fecha_especifica,
        )
        tablas_json = json.dumps(data.tablas)

        async with pool.acquire() as conn:
            if empresa_id:
                row = await conn.fetchrow(
                    """
                    INSERT INTO backup_configuracion (
                        empresa_id, activo, frecuencia, fecha_inicio, fecha_especifica,
                        hora_ejecucion, dia_semana, dia_mes, destino, formato, tablas,
                        retencion_dias, proxima_ejecucion, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13, now())
                    ON CONFLICT (empresa_id) DO UPDATE SET
                        activo = EXCLUDED.activo,
                        frecuencia = EXCLUDED.frecuencia,
                        fecha_inicio = EXCLUDED.fecha_inicio,
                        fecha_especifica = EXCLUDED.fecha_especifica,
                        hora_ejecucion = EXCLUDED.hora_ejecucion,
                        dia_semana = EXCLUDED.dia_semana,
                        dia_mes = EXCLUDED.dia_mes,
                        destino = EXCLUDED.destino,
                        formato = EXCLUDED.formato,
                        tablas = EXCLUDED.tablas,
                        retencion_dias = EXCLUDED.retencion_dias,
                        proxima_ejecucion = EXCLUDED.proxima_ejecucion,
                        updated_at = now()
                    RETURNING *
                    """,
                    UUID(empresa_id),
                    data.activo,
                    data.frecuencia,
                    data.fecha_inicio,
                    data.fecha_especifica,
                    data.hora_ejecucion,
                    data.dia_semana,
                    data.dia_mes,
                    data.destino,
                    data.formato,
                    tablas_json,
                    data.retencion_dias,
                    proxima,
                )
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO backup_configuracion (
                        empresa_id, activo, frecuencia, fecha_inicio, fecha_especifica,
                        hora_ejecucion, dia_semana, dia_mes, destino, formato, tablas,
                        retencion_dias, proxima_ejecucion, updated_at
                    ) VALUES (NULL, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, now())
                    ON CONFLICT ((1)) WHERE empresa_id IS NULL DO UPDATE SET
                        activo = EXCLUDED.activo,
                        frecuencia = EXCLUDED.frecuencia,
                        fecha_inicio = EXCLUDED.fecha_inicio,
                        fecha_especifica = EXCLUDED.fecha_especifica,
                        hora_ejecucion = EXCLUDED.hora_ejecucion,
                        dia_semana = EXCLUDED.dia_semana,
                        dia_mes = EXCLUDED.dia_mes,
                        destino = EXCLUDED.destino,
                        formato = EXCLUDED.formato,
                        tablas = EXCLUDED.tablas,
                        retencion_dias = EXCLUDED.retencion_dias,
                        proxima_ejecucion = EXCLUDED.proxima_ejecucion,
                        updated_at = now()
                    RETURNING *
                    """,
                    data.activo,
                    data.frecuencia,
                    data.fecha_inicio,
                    data.fecha_especifica,
                    data.hora_ejecucion,
                    data.dia_semana,
                    data.dia_mes,
                    data.destino,
                    data.formato,
                    tablas_json,
                    data.retencion_dias,
                    proxima,
                )

        if current_user:
            try:
                await audit_event(
                    empresa_id=current_user.empresa_id,
                    usuario_id=current_user.user_id,
                    actor_tipo=current_user.rol,
                    accion="UPDATE",
                    entidad="backup_configuracion",
                    entidad_id=str(row["id"]),
                    datos_despues=data.model_dump(),
                    es_accion_superadmin=(current_user.rol == "superadmin"),
                )
            except Exception:
                logger.warning("No se pudo auditar la configuracion de backup")

        tablas_list = row["tablas"]
        if isinstance(tablas_list, str):
            tablas_list = json.loads(tablas_list)

        return BackupConfiguracionOut(
            id=str(row["id"]),
            empresa_id=str(row["empresa_id"]) if row["empresa_id"] else None,
            activo=row["activo"],
            frecuencia=row["frecuencia"],
            fecha_inicio=row["fecha_inicio"],
            fecha_especifica=row["fecha_especifica"],
            hora_ejecucion=row["hora_ejecucion"],
            dia_semana=row["dia_semana"],
            dia_mes=row["dia_mes"] or 1,
            destino=row["destino"],
            formato=row["formato"],
            tablas=tablas_list,
            retencion_dias=row["retencion_dias"],
            ultima_ejecucion=row["ultima_ejecucion"],
            proxima_ejecucion=row["proxima_ejecucion"],
            estado_ultima_ejecucion=row["estado_ultima_ejecucion"],
            error_ultima_ejecucion=row["error_ultima_ejecucion"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    async def create_backup(
        current_user: CurrentUser | None,
        data: BackupManualCreate,
        tipo: str = "manual",
        force_empresa_id: str | None = None,
    ) -> BackupRegistroOut:
        pool = get_pool()

        # Determinar alcance y empresa_id
        is_superadmin = (current_user and current_user.rol == "superadmin")
        target_empresa_id: str | None = None

        if force_empresa_id:
            target_empresa_id = force_empresa_id
            alcance = "empresa"
        elif is_superadmin:
            if data.alcance == "global":
                target_empresa_id = None
                alcance = "global"
            elif data.empresa_id:
                target_empresa_id = data.empresa_id
                alcance = "empresa"
            else:
                target_empresa_id = None
                alcance = "global"
        else:
            if not current_user or not current_user.empresa_id:
                raise api_error(403, "EMPRESA_REQUERIDA", "Se requiere ID de empresa")
            target_empresa_id = current_user.empresa_id
            alcance = "empresa"

        # Determinar tablas a respaldar
        selected_tables: list[str] = []
        if data.modulos:
            all_mods = MODULOS_CATALOGO.copy()
            if is_superadmin:
                all_mods["saas_global"] = MODULO_SAAS_GLOBAL
            for mod_id in data.modulos:
                if mod_id in all_mods:
                    selected_tables.extend(all_mods[mod_id].tablas)

        if data.tablas:
            selected_tables.extend(data.tablas)

        if not selected_tables:
            # Si no seleccionó nada, respaldar módulos estándar
            for mod_id in ["catalogo", "inventario", "ventas", "reservas", "clientes"]:
                selected_tables.extend(MODULOS_CATALOGO[mod_id].tablas)

        if data.incluir_auditoria and "bitacora_auditoria" not in selected_tables:
            selected_tables.append("bitacora_auditoria")

        # Eliminar duplicados manteniendo orden
        ordered_tables: list[str] = []
        for t in selected_tables:
            if t not in ordered_tables:
                ordered_tables.append(t)

        now_utc = datetime.now(timezone.utc)
        timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S")
        suffix = uuid4().hex[:6]
        scope_prefix = f"tenant_{target_empresa_id[:8]}" if target_empresa_id else "global_saas"
        default_name = f"backup_{scope_prefix}_{timestamp_str}_{suffix}"
        nombre = data.nombre.strip() if data.nombre and data.nombre.strip() else default_name

        # Recolectar datos de las tablas
        dump_data: dict[str, list[dict[str, Any]]] = {}
        tables_summary: dict[str, int] = {}
        total_registros = 0

        async with pool.acquire() as conn:
            # Obtener nombre de la empresa si aplica
            empresa_nombre = None
            if target_empresa_id:
                emp_row = await conn.fetchrow(
                    "SELECT nombre FROM empresa WHERE id = $1", UUID(target_empresa_id)
                )
                if emp_row:
                    empresa_nombre = emp_row["nombre"]

            # Verificar qué tablas existen realmente y cuáles tienen columna empresa_id
            for tbl in ordered_tables:
                # Comprobar si la tabla existe en public
                table_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = $1
                    )
                    """,
                    tbl,
                )
                if not table_exists:
                    continue

                has_empresa_col = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = $1 AND column_name = 'empresa_id'
                    )
                    """,
                    tbl,
                )

                try:
                    if target_empresa_id and has_empresa_col:
                        rows = await conn.fetch(
                            f"SELECT * FROM {tbl} WHERE empresa_id = $1",
                            UUID(target_empresa_id),
                        )
                    else:
                        # Si es global o la tabla no tiene empresa_id
                        rows = await conn.fetch(f"SELECT * FROM {tbl} LIMIT 5000")

                    serialized_rows = [
                        {k: v for k, v in dict(r).items()} for r in rows
                    ]
                    dump_data[tbl] = serialized_rows
                    tables_summary[tbl] = len(serialized_rows)
                    total_registros += len(serialized_rows)
                except Exception as ex:
                    logger.warning("No se pudo exportar la tabla %s: %s", tbl, ex)
                    tables_summary[tbl] = 0

        # Serializar según formato
        ext = "json" if data.formato == "json" else "sql"
        filename = f"{nombre}.{ext}"

        if data.formato == "json":
            backup_payload = {
                "metadata": {
                    "backup_id": str(uuid4()),
                    "nombre": nombre,
                    "descripcion": data.descripcion,
                    "tipo": tipo,
                    "alcance": alcance,
                    "empresa_id": target_empresa_id,
                    "empresa_nombre": empresa_nombre,
                    "creado_por": current_user.user_id if current_user else "sistema_automatico",
                    "timestamp": now_utc.isoformat(),
                    "total_tablas": len(dump_data),
                    "total_registros": total_registros,
                    "formato": "json",
                },
                "tables_summary": tables_summary,
                "data": dump_data,
            }
            content_str = json.dumps(
                backup_payload,
                default=_custom_json_serializer,
                indent=2,
                ensure_ascii=False,
            )
            content_bytes = content_str.encode("utf-8")
        else:
            # Formato SQL
            lines = [
                f"-- FASHIONSTORE BACKUP: {nombre}",
                f"-- Alcance: {alcance.upper()} | Tipo: {tipo.upper()}",
                f"-- Fecha: {now_utc.isoformat()}",
                f"-- Empresa: {empresa_nombre or 'Sistema Global'}",
                f"-- Registros Totales: {total_registros}",
                "BEGIN;\n",
            ]
            for tbl, rows in dump_data.items():
                if not rows:
                    continue
                lines.append(f"-- Tabla: {tbl} ({len(rows)} registros)")
                for r in rows:
                    cols = list(r.keys())
                    vals = []
                    for col in cols:
                        val = r[col]
                        if val is None:
                            vals.append("NULL")
                        elif isinstance(val, (int, float, Decimal)):
                            vals.append(str(val))
                        elif isinstance(val, bool):
                            vals.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (dict, list)):
                            serialized_json = json.dumps(val, default=_custom_json_serializer).replace("'", "''")
                            vals.append(f"'{serialized_json}'::jsonb")
                        else:
                            clean_str = str(_custom_json_serializer(val) if not isinstance(val, str) else val)
                            vals.append("'" + clean_str.replace("'", "''") + "'")
                    cols_str = ", ".join(f'"{c}"' for c in cols)
                    vals_str = ", ".join(vals)
                    lines.append(f'INSERT INTO {tbl} ({cols_str}) VALUES ({vals_str}) ON CONFLICT DO NOTHING;')
                lines.append("")
            lines.append("COMMIT;")
            content_str = "\n".join(lines)
            content_bytes = content_str.encode("utf-8")

        # Calcular Checksum SHA256 y Tamaño
        checksum = hashlib.sha256(content_bytes).hexdigest()
        tamano_bytes = len(content_bytes)
        tamano_legible = _format_size(tamano_bytes)

        # Destinos de Guardado: Localhost y Nube
        save_local = data.destino in ("local", "ambos")
        save_nube = data.destino in ("nube", "ambos")

        local_file_path = LOCAL_STORAGE_DIR / filename
        cloud_file_path = CLOUD_STORAGE_DIR / filename

        ruta_local_rel: str | None = None
        url_nube_str: str | None = None

        if save_local:
            local_file_path.write_bytes(content_bytes)
            ruta_local_rel = f"backups/local/{filename}"

        if save_nube:
            cloud_file_path.write_bytes(content_bytes)
            url_nube_str = f"s3://{CLOUD_BUCKET_NAME}/cloud/{filename}"

        backup_id = uuid4()
        usuario_id = UUID(current_user.user_id) if current_user and current_user.user_id else None

        # Insertar registro en BD
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO backup_registro (
                    id, empresa_id, usuario_id, nombre, descripcion, tipo, alcance,
                    formato, tablas_seleccionadas, tamano_bytes, tamano_legible,
                    total_registros, checksum_sha256, guardado_local, ruta_local,
                    guardado_nube, url_nube, proveedor_nube, estado, detalles_tablas,
                    metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7,
                    $8, $9::jsonb, $10, $11,
                    $12, $13, $14, $15,
                    $16, $17, $18, 'completado', $19::jsonb,
                    $20::jsonb, $21
                )
                RETURNING *
                """,
                backup_id,
                UUID(target_empresa_id) if target_empresa_id else None,
                usuario_id,
                nombre,
                data.descripcion,
                tipo,
                alcance,
                data.formato,
                json.dumps(ordered_tables),
                tamano_bytes,
                tamano_legible,
                total_registros,
                checksum,
                save_local,
                ruta_local_rel,
                save_nube,
                url_nube_str,
                CLOUD_PROVIDER_NAME,
                json.dumps(tables_summary),
                json.dumps({
                    "cloud_bucket": CLOUD_BUCKET_NAME,
                    "cloud_provider": CLOUD_PROVIDER_NAME,
                    "compression": "none",
                }),
                now_utc,
            )

        if current_user:
            try:
                await audit_event(
                    empresa_id=target_empresa_id,
                    usuario_id=current_user.user_id,
                    actor_tipo=current_user.rol,
                    accion="BACKUP",
                    entidad="backup_registro",
                    entidad_id=str(backup_id),
                    datos_despues={
                        "nombre": nombre,
                        "tipo": tipo,
                        "alcance": alcance,
                        "formato": data.formato,
                        "destino": data.destino,
                        "tamano": tamano_legible,
                        "total_registros": total_registros,
                    },
                    es_accion_superadmin=is_superadmin,
                )
            except Exception:
                logger.warning("No se pudo auditar la creación del backup")

        tablas_arr = row["tablas_seleccionadas"]
        if isinstance(tablas_arr, str):
            tablas_arr = json.loads(tablas_arr)

        detalles_dict = row["detalles_tablas"]
        if isinstance(detalles_dict, str):
            detalles_dict = json.loads(detalles_dict)

        return BackupRegistroOut(
            id=str(row["id"]),
            empresa_id=str(row["empresa_id"]) if row["empresa_id"] else None,
            empresa_nombre=empresa_nombre,
            usuario_id=str(row["usuario_id"]) if row["usuario_id"] else None,
            usuario_nombre=current_user.rol if current_user else "Sistema Automático",
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            tipo=row["tipo"],
            alcance=row["alcance"],
            formato=row["formato"],
            tablas_seleccionadas=tablas_arr or [],
            tamano_bytes=row["tamano_bytes"],
            tamano_legible=row["tamano_legible"],
            total_registros=row["total_registros"],
            checksum_sha256=row["checksum_sha256"],
            guardado_local=row["guardado_local"],
            ruta_local=row["ruta_local"],
            guardado_nube=row["guardado_nube"],
            url_nube=row["url_nube"],
            proveedor_nube=row["proveedor_nube"],
            estado=row["estado"],
            detalles_tablas=detalles_dict or {},
            metadata={},
            created_at=row["created_at"],
        )

    @staticmethod
    async def list_backups(
        current_user: CurrentUser,
        tipo: str | None = None,
        destino: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BackupListResponse:
        pool = get_pool()
        is_superadmin = (current_user.rol == "superadmin")
        empresa_id = current_user.empresa_id

        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if not is_superadmin:
            if not empresa_id:
                return BackupListResponse(items=[], total=0, page=page, page_size=page_size)
            conditions.append(f"b.empresa_id = ${idx}")
            params.append(UUID(empresa_id))
            idx += 1

        if tipo in ("manual", "automatico"):
            conditions.append(f"b.tipo = ${idx}")
            params.append(tipo)
            idx += 1

        if destino == "local":
            conditions.append("b.guardado_local = true")
        elif destino == "nube":
            conditions.append("b.guardado_nube = true")

        if search and search.strip():
            conditions.append(f"(b.nombre ILIKE ${idx} OR b.descripcion ILIKE ${idx})")
            params.append(f"%{search.strip()}%")
            idx += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        count_sql = f"SELECT count(*) FROM backup_registro b {where_clause}"

        select_sql = f"""
            SELECT b.id, b.empresa_id, b.usuario_id, b.nombre, b.descripcion,
                   b.tipo, b.alcance, b.formato, b.tablas_seleccionadas,
                   b.tamano_bytes, b.tamano_legible, b.total_registros,
                   b.checksum_sha256, b.guardado_local, b.ruta_local,
                   b.guardado_nube, b.url_nube, b.proveedor_nube, b.estado,
                   b.error_mensaje, b.detalles_tablas, b.created_at,
                   e.nombre AS empresa_nombre,
                   u.nombre AS usuario_nombre
            FROM backup_registro b
            LEFT JOIN empresa e ON e.id = b.empresa_id
            LEFT JOIN usuario u ON u.id = b.usuario_id
            {where_clause}
            ORDER BY b.created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """

        offset = (page - 1) * page_size
        params_with_paging = list(params) + [page_size, offset]

        async with pool.acquire() as conn:
            total = await conn.fetchval(count_sql, *params)
            rows = await conn.fetch(select_sql, *params_with_paging)

        items: list[BackupRegistroOut] = []
        for r in rows:
            tablas_arr = r["tablas_seleccionadas"]
            if isinstance(tablas_arr, str):
                tablas_arr = json.loads(tablas_arr)
            detalles_dict = r["detalles_tablas"]
            if isinstance(detalles_dict, str):
                detalles_dict = json.loads(detalles_dict)

            items.append(
                BackupRegistroOut(
                    id=str(r["id"]),
                    empresa_id=str(r["empresa_id"]) if r["empresa_id"] else None,
                    empresa_nombre=r["empresa_nombre"],
                    usuario_id=str(r["usuario_id"]) if r["usuario_id"] else None,
                    usuario_nombre=r["usuario_nombre"],
                    nombre=r["nombre"],
                    descripcion=r["descripcion"],
                    tipo=r["tipo"],
                    alcance=r["alcance"],
                    formato=r["formato"],
                    tablas_seleccionadas=tablas_arr or [],
                    tamano_bytes=r["tamano_bytes"],
                    tamano_legible=r["tamano_legible"],
                    total_registros=r["total_registros"],
                    checksum_sha256=r["checksum_sha256"],
                    guardado_local=r["guardado_local"],
                    ruta_local=r["ruta_local"],
                    guardado_nube=r["guardado_nube"],
                    url_nube=r["url_nube"],
                    proveedor_nube=r["proveedor_nube"],
                    estado=r["estado"],
                    error_mensaje=r["error_mensaje"],
                    detalles_tablas=detalles_dict or {},
                    metadata={},
                    created_at=r["created_at"],
                )
            )

        return BackupListResponse(
            items=items,
            total=total or 0,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    async def get_backup(current_user: CurrentUser, backup_id: str) -> BackupRegistroOut:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT b.*, e.nombre AS empresa_nombre, u.nombre AS usuario_nombre
                FROM backup_registro b
                LEFT JOIN empresa e ON e.id = b.empresa_id
                LEFT JOIN usuario u ON u.id = b.usuario_id
                WHERE b.id = $1
                """,
                UUID(backup_id),
            )

        if not row:
            raise api_error(404, "BACKUP_NO_ENCONTRADO", "El backup especificado no existe")

        is_superadmin = (current_user.rol == "superadmin")
        if not is_superadmin and row["empresa_id"] and str(row["empresa_id"]) != current_user.empresa_id:
            raise api_error(403, "NO_AUTORIZADO", "No tiene acceso a este backup")

        tablas_arr = row["tablas_seleccionadas"]
        if isinstance(tablas_arr, str):
            tablas_arr = json.loads(tablas_arr)
        detalles_dict = row["detalles_tablas"]
        if isinstance(detalles_dict, str):
            detalles_dict = json.loads(detalles_dict)

        return BackupRegistroOut(
            id=str(row["id"]),
            empresa_id=str(row["empresa_id"]) if row["empresa_id"] else None,
            empresa_nombre=row["empresa_nombre"],
            usuario_id=str(row["usuario_id"]) if row["usuario_id"] else None,
            usuario_nombre=row["usuario_nombre"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            tipo=row["tipo"],
            alcance=row["alcance"],
            formato=row["formato"],
            tablas_seleccionadas=tablas_arr or [],
            tamano_bytes=row["tamano_bytes"],
            tamano_legible=row["tamano_legible"],
            total_registros=row["total_registros"],
            checksum_sha256=row["checksum_sha256"],
            guardado_local=row["guardado_local"],
            ruta_local=row["ruta_local"],
            guardado_nube=row["guardado_nube"],
            url_nube=row["url_nube"],
            proveedor_nube=row["proveedor_nube"],
            estado=row["estado"],
            error_mensaje=row["error_mensaje"],
            detalles_tablas=detalles_dict or {},
            metadata={},
            created_at=row["created_at"],
        )

    @staticmethod
    async def get_backup_file_data(
        current_user: CurrentUser, backup_id: str, location: str = "local"
    ) -> tuple[Path, str, str]:
        backup = await BackupService.get_backup(current_user, backup_id)
        filename = f"{backup.nombre}.{backup.formato}"

        if location == "cloud":
            path = CLOUD_STORAGE_DIR / filename
            if not path.exists():
                # Fallback a local si no está en cloud
                path = LOCAL_STORAGE_DIR / filename
        else:
            path = LOCAL_STORAGE_DIR / filename
            if not path.exists():
                # Fallback a cloud
                path = CLOUD_STORAGE_DIR / filename

        if not path.exists():
            raise api_error(404, "ARCHIVO_NO_ENCONTRADO", "El archivo físico del backup no fue encontrado")

        content_type = "application/json" if backup.formato == "json" else "application/sql"
        return path, filename, content_type

    @staticmethod
    async def sync_to_cloud(current_user: CurrentUser, backup_id: str) -> BackupRegistroOut:
        backup = await BackupService.get_backup(current_user, backup_id)
        filename = f"{backup.nombre}.{backup.formato}"
        local_path = LOCAL_STORAGE_DIR / filename
        cloud_path = CLOUD_STORAGE_DIR / filename

        if not local_path.exists():
            raise api_error(400, "ARCHIVO_LOCAL_NO_EXISTE", "No existe archivo local para sincronizar")

        shutil.copy2(local_path, cloud_path)
        cloud_url = f"s3://{CLOUD_BUCKET_NAME}/cloud/{filename}"

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE backup_registro
                SET guardado_nube = true, url_nube = $1, proveedor_nube = $2
                WHERE id = $3
                """,
                cloud_url,
                CLOUD_PROVIDER_NAME,
                UUID(backup_id),
            )

        return await BackupService.get_backup(current_user, backup_id)

    @staticmethod
    async def sync_to_local(current_user: CurrentUser, backup_id: str) -> BackupRegistroOut:
        backup = await BackupService.get_backup(current_user, backup_id)
        filename = f"{backup.nombre}.{backup.formato}"
        local_path = LOCAL_STORAGE_DIR / filename
        cloud_path = CLOUD_STORAGE_DIR / filename

        if not cloud_path.exists():
            raise api_error(400, "ARCHIVO_NUBE_NO_EXISTE", "No existe archivo en la nube para descargar a local")

        shutil.copy2(cloud_path, local_path)
        ruta_local = f"backups/local/{filename}"

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE backup_registro
                SET guardado_local = true, ruta_local = $1
                WHERE id = $2
                """,
                ruta_local,
                UUID(backup_id),
            )

        return await BackupService.get_backup(current_user, backup_id)

    @staticmethod
    async def delete_backup(current_user: CurrentUser, backup_id: str) -> dict[str, Any]:
        backup = await BackupService.get_backup(current_user, backup_id)
        filename = f"{backup.nombre}.{backup.formato}"

        local_path = LOCAL_STORAGE_DIR / filename
        if local_path.exists():
            try:
                local_path.unlink()
            except Exception as e:
                logger.warning("No se pudo eliminar archivo local: %s", e)

        cloud_path = CLOUD_STORAGE_DIR / filename
        if cloud_path.exists():
            try:
                cloud_path.unlink()
            except Exception as e:
                logger.warning("No se pudo eliminar archivo cloud: %s", e)

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM backup_registro WHERE id = $1", UUID(backup_id))

        return {"status": "ok", "mensaje": "Backup eliminado correctamente", "id": backup_id}

    @staticmethod
    async def restore_backup(
        current_user: CurrentUser,
        backup_id: str,
        data: BackupRestaurarRequest,
    ) -> dict[str, Any]:
        backup = await BackupService.get_backup(current_user, backup_id)
        file_path, filename, _ = await BackupService.get_backup_file_data(current_user, backup_id)

        pool = get_pool()

        if backup.formato == "json":
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception as ex:
                raise api_error(400, "BACKUP_CORRUPTO", f"No se pudo leer el archivo JSON: {ex}")

            tables_data: dict[str, list[dict]] = payload.get("data", {})
            tables_to_restore = data.tablas or list(tables_data.keys())

            restored_summary: dict[str, int] = {}
            total_restored = 0

            async with pool.acquire() as conn:
                async with conn.transaction():
                    for tbl in tables_to_restore:
                        if tbl not in tables_data:
                            continue
                        rows = tables_data[tbl]
                        if not rows:
                            restored_summary[tbl] = 0
                            continue

                        # Restaurar registros fila por fila de forma segura
                        count = 0
                        for r in rows:
                            cols = list(r.keys())
                            cols_escaped = ", ".join(f'"{c}"' for c in cols)
                            placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
                            values = list(r.values())

                            insert_query = f"""
                                INSERT INTO {tbl} ({cols_escaped})
                                VALUES ({placeholders})
                                ON CONFLICT DO NOTHING
                            """
                            try:
                                await conn.execute(insert_query, *values)
                                count += 1
                            except Exception as ex:
                                logger.debug("Omitiendo registro en %s por conflicto: %s", tbl, ex)

                        restored_summary[tbl] = count
                        total_restored += count

            return {
                "status": "ok",
                "mensaje": f"Restauración completada. {total_restored} registros procesados en {len(restored_summary)} tablas.",
                "backup_id": backup_id,
                "tablas_restauradas": restored_summary,
                "total_registros": total_restored,
            }
        else:
            # SQL restore
            sql_content = file_path.read_text(encoding="utf-8")
            async with pool.acquire() as conn:
                await conn.execute(sql_content)

            return {
                "status": "ok",
                "mensaje": "Script SQL ejecutado con éxito.",
                "backup_id": backup_id,
            }

    @staticmethod
    async def get_estadisticas(current_user: CurrentUser) -> BackupEstadisticasOut:
        pool = get_pool()
        is_superadmin = (current_user.rol == "superadmin")
        empresa_id = current_user.empresa_id

        where = ""
        params: list[Any] = []
        if not is_superadmin:
            if empresa_id:
                where = "WHERE empresa_id = $1"
                params.append(UUID(empresa_id))
            else:
                where = "WHERE false"

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT
                    count(*)::int AS total_backups,
                    count(*) FILTER (WHERE guardado_local = true)::int AS total_locales,
                    count(*) FILTER (WHERE guardado_nube = true)::int AS total_nube,
                    count(*) FILTER (WHERE tipo = 'automatico')::int AS total_automaticos,
                    count(*) FILTER (WHERE tipo = 'manual')::int AS total_manuales,
                    coalesce(sum(tamano_bytes) FILTER (WHERE guardado_local = true), 0)::bigint AS espacio_local_bytes,
                    coalesce(sum(tamano_bytes) FILTER (WHERE guardado_nube = true), 0)::bigint AS espacio_nube_bytes,
                    max(created_at) AS ultimo_backup
                FROM backup_registro
                {where}
                """,
                *params,
            )

            # Obtener estado de config auto
            if not is_superadmin and empresa_id:
                cfg = await conn.fetchrow(
                    "SELECT activo, proxima_ejecucion FROM backup_configuracion WHERE empresa_id = $1",
                    UUID(empresa_id),
                )
            else:
                cfg = await conn.fetchrow(
                    "SELECT activo, proxima_ejecucion FROM backup_configuracion WHERE empresa_id IS NULL"
                )

        espacio_local = int(row["espacio_local_bytes"]) if row else 0
        espacio_nube = int(row["espacio_nube_bytes"]) if row else 0

        return BackupEstadisticasOut(
            total_backups=row["total_backups"] if row else 0,
            total_locales=row["total_locales"] if row else 0,
            total_nube=row["total_nube"] if row else 0,
            total_automaticos=row["total_automaticos"] if row else 0,
            total_manuales=row["total_manuales"] if row else 0,
            espacio_local_bytes=espacio_local,
            espacio_local_legible=_format_size(espacio_local),
            espacio_nube_bytes=espacio_nube,
            espacio_nube_legible=_format_size(espacio_nube),
            proveedor_nube=CLOUD_PROVIDER_NAME,
            ultimo_backup=row["ultimo_backup"] if row else None,
            auto_backup_activo=cfg["activo"] if cfg else False,
            proximo_auto_backup=cfg["proxima_ejecucion"] if cfg else None,
        )

    @staticmethod
    async def run_scheduled_backups(force: bool = False, force_empresa_id: str | None = None) -> list[str]:
        pool = get_pool()
        now = datetime.now(timezone.utc)

        async with pool.acquire() as conn:
            if force:
                if force_empresa_id:
                    configs = await conn.fetch(
                        """
                        SELECT id, empresa_id, frecuencia, hora_ejecucion, dia_semana, dia_mes,
                               fecha_inicio, fecha_especifica, destino, formato, tablas,
                               retencion_dias, proxima_ejecucion
                        FROM backup_configuracion
                        WHERE empresa_id = $1
                        """,
                        UUID(force_empresa_id),
                    )
                else:
                    configs = await conn.fetch(
                        """
                        SELECT id, empresa_id, frecuencia, hora_ejecucion, dia_semana, dia_mes,
                               fecha_inicio, fecha_especifica, destino, formato, tablas,
                               retencion_dias, proxima_ejecucion
                        FROM backup_configuracion
                        WHERE empresa_id IS NULL OR activo = true
                        """
                    )
            else:
                configs = await conn.fetch(
                    """
                    SELECT id, empresa_id, frecuencia, hora_ejecucion, dia_semana, dia_mes,
                           fecha_inicio, fecha_especifica, destino, formato, tablas,
                           retencion_dias, proxima_ejecucion
                    FROM backup_configuracion
                    WHERE activo = true
                      AND (proxima_ejecucion IS NULL OR proxima_ejecucion <= $1)
                    """,
                    now,
                )

        executed_ids: list[str] = []

        for cfg in configs:
            cfg_id = cfg["id"]
            empresa_id = str(cfg["empresa_id"]) if cfg["empresa_id"] else None
            destino = cfg["destino"] or "ambos"
            formato = cfg["formato"] or "json"
            tablas_val = cfg["tablas"]
            if isinstance(tablas_val, str):
                tablas_val = json.loads(tablas_val)

            create_req = BackupManualCreate(
                nombre=f"auto_backup_{empresa_id[:8] if empresa_id else 'saas'}_{now.strftime('%Y%m%d_%H%M%S')}",
                descripcion="Respaldo automático programado por el sistema",
                alcance="empresa" if empresa_id else "global",
                empresa_id=empresa_id,
                formato=formato,
                destino=destino,
                modulos=tablas_val if isinstance(tablas_val, list) else None,
            )

            try:
                res = await BackupService.create_backup(
                    current_user=None,
                    data=create_req,
                    tipo="automatico",
                    force_empresa_id=empresa_id,
                )
                executed_ids.append(res.id)

                # Calcular siguiente ejecución
                next_run = _calculate_next_run(
                    frecuencia=cfg["frecuencia"],
                    hora_str=cfg["hora_ejecucion"],
                    dia_semana=cfg["dia_semana"],
                    dia_mes=cfg["dia_mes"] or 1,
                    fecha_inicio=cfg["fecha_inicio"],
                    fecha_especifica=cfg["fecha_especifica"],
                    from_time=now,
                )

                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE backup_configuracion
                        SET ultima_ejecucion = $1,
                            estado_ultima_ejecucion = 'exitoso',
                            error_ultima_ejecucion = NULL,
                            proxima_ejecucion = $2,
                            updated_at = now()
                        WHERE id = $3
                        """,
                        now,
                        next_run,
                        cfg_id,
                    )
            except Exception as ex:
                logger.exception("Error al ejecutar backup automatico para config %s: %s", cfg_id, ex)
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE backup_configuracion
                        SET ultima_ejecucion = $1,
                            estado_ultima_ejecucion = 'fallido',
                            error_ultima_ejecucion = $2,
                            updated_at = now()
                        WHERE id = $3
                        """,
                        now,
                        str(ex),
                        cfg_id,
                    )

        return executed_ids
