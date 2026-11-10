import base64
import io
import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import httpx
from asyncpg import Connection
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.inteligencia import (
    ExportarReporteRequest,
    ExportarReporteResponse,
    ReporteIaRequest,
    ReporteIaResponse,
)

logger = logging.getLogger(__name__)


def _get_llm_config() -> Tuple[str, str, str]:
    settings = get_settings()
    api_key = (os.environ.get("LLM_API_KEY") or settings.llm_api_key or "").strip()
    model = (os.environ.get("LLM_MODEL") or settings.llm_model or "gpt-4o-mini").strip()
    api_url = (
        os.environ.get("LLM_API_URL")
        or settings.llm_api_url
        or "https://api.openai.com/v1/chat/completions"
    ).strip()
    return api_key, model, api_url


# ---------------------------------------------------------------------------
# Whitelist de Reportes Permitidos (Regla BR-08)
# ---------------------------------------------------------------------------
WHITELIST_INTENTS = {
    "ventas_por_sucursal": [
        r"ventas.*sucursal",
        r"sucursales.*ventas",
        r"ventas.*agrupadas.*sucursal",
        r"compar[aá].*sucursales",
    ],
    "top_productos_vendidos": [
        r"(diez|10|top|mejores|m[aá]s vendidos).*productos",
        r"productos.*m[aá]s vendidos",
        r"prendas.*m[aá]s vendidas",
        r"top.*prendas",
    ],
    "ventas_temporales_semana": [
        r"ventas.*semana",
        r"gr[aá]fico.*ventas",
        r"evoluci[oó]n.*ventas",
        r"ventas.*mes",
        r"tendencia.*ventas",
    ],
    "rotacion_stock_critico": [
        r"rotaci[oó]n",
        r"stock.*cr[ií]tico",
        r"stock.*bajo",
        r"alerta.*inventario",
        r"existencias.*categor[ií]a",
    ],
    "analisis_canales_pago": [
        r"m[eé]todos?.*pago",
        r"canales?.*venta",
        r"efectivo.*tarjeta",
        r"pos.*online",
        r"pasarela.*pagos",
    ],
}


async def validar_plan_profesional(conn: Connection, empresa_id: UUID) -> None:
    """Valida que la empresa tenga plan Profesional o cuota IA habilitada (BR-03)."""
    row = await conn.fetchrow(
        """
        SELECT p.codigo,
               s.estado,
               (
                   SELECT pl.limite
                     FROM plan_limite pl
                    WHERE pl.plan_id = p.id
                      AND pl.recurso = 'consultas_ia_mes'
                    LIMIT 1
               ) AS limite_ia
          FROM suscripcion s
          JOIN plan p ON p.id = s.plan_id
         WHERE s.empresa_id = $1
           AND s.estado IN ('activa', 'prueba', 'mora')
         ORDER BY s.fecha_inicio DESC, s.created_at DESC
         LIMIT 1
        """,
        empresa_id,
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los reportes generativos con Inteligencia Artificial requieren una suscripción activa en plan 'Profesional' (BR-03).",
        )

    codigo = str(row["codigo"] or "").lower()
    limite_ia = row.get("limite_ia") if hasattr(row, "get") else row["limite_ia"]
    habilitado_por_codigo = codigo in ("profesional", "enterprise", "pro")
    habilitado_por_limite = limite_ia is None or int(limite_ia) > 0
    if not habilitado_por_codigo and not (limite_ia is not None and habilitado_por_limite):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los reportes generativos con Inteligencia Artificial requieren el plan 'Profesional' (BR-03 y Sección 9.4).",
        )


def _strip_json_fences(raw: str) -> str:
    txt = raw.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```(?:json)?\s*", "", txt)
        txt = re.sub(r"\s*```$", "", txt)
    return txt.strip()


def _extract_common_params(prompt: str) -> Dict[str, Any]:
    p_lower = prompt.lower().strip()
    parametros: Dict[str, Any] = {"limite": 10}
    meses_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    for mes_nombre, mes_num in meses_map.items():
        if mes_nombre in p_lower:
            year = datetime.now().year
            parametros["mes"] = mes_num
            parametros["mes_nombre"] = mes_nombre.capitalize()
            parametros["fecha_inicio"] = date(year, mes_num, 1)
            next_month = mes_num + 1 if mes_num < 12 else 1
            next_year = year if mes_num < 12 else year + 1
            parametros["fecha_fin"] = date(next_year, next_month, 1) - timedelta(days=1)
            break

    if "diez" in p_lower or "10" in p_lower:
        parametros["limite"] = 10
    elif "cinco" in p_lower or "5" in p_lower:
        parametros["limite"] = 5
    elif "veinte" in p_lower or "20" in p_lower:
        parametros["limite"] = 20
    return parametros


_BLOCKED_SQL_PATTERNS = re.compile(
    r"(?:"
    r"\bdrop\s+(?:table|database|schema|view)\b"
    r"|\btruncate\s+(?:table\s+)?\w+"
    r"|\bdelete\s+from\s+\w+"
    r"|\binsert\s+into\s+\w+"
    r"|\bupdate\s+\w+\s+set\b"
    r"|\balter\s+table\s+\w+"
    r"|\bunion\s+(?:all\s+)?select\b"
    r"|\bselect\b.{1,80}\bfrom\s+\w+"
    r"|;\s*--"
    r")",
    re.IGNORECASE,
)


def _reject_disallowed_prompt() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "La consulta formulada no coincide con los reportes analíticos de la whitelist autorizada (BR-08). "
            "Nunca se ejecuta SQL libre generado por el usuario o LLM. "
            "Ejemplos permitidos: 'Ventas de septiembre agrupadas por sucursal', "
            "'¿Cuáles fueron los 10 productos más vendidos?', "
            "'Generá un gráfico de ventas por semana', "
            "'Rotación y stock crítico por categoría'."
        ),
    )


async def clasificar_intencion_con_llm(prompt: str) -> Tuple[str, Dict[str, Any], str]:
    """
    Adaptador LLM OpenAI-compatible (BR-08): traduce lenguaje natural exclusivamente
    a una de las intenciones fijas de WHITELIST_INTENTS (nunca SQL libre).
    Si LLM_API_KEY no está configurada o el proveedor falla, usa el clasificador regex local.
    """
    if _BLOCKED_SQL_PATTERNS.search(prompt or ""):
        _reject_disallowed_prompt()

    api_key, model, api_url = _get_llm_config()
    if not api_key:
        intent, params = clasificar_intencion_whitelist(prompt)
        return intent, params, "whitelist-regex-fallback"

    intents_permitidos = sorted(WHITELIST_INTENTS.keys())
    system_prompt = (
        "Eres un enrutador estricto de reportes BI bajo whitelist BR-08. "
        "NUNCA generes SQL ni código ejecutable. "
        f"Debes responder ÚNICAMENTE un JSON válido con las claves: "
        f'{{"intent": <uno de {intents_permitidos} o "rechazado">, "mes": <1..12 o null>, "limite": <int 1..50 o 10>}}. '
        "Si el usuario pide modificar datos, volcar tablas arbitrarias, SQL o algo fuera de los intents permitidos, "
        'responde {"intent": "rechazado", "mes": null, "limite": 10}.'
    )

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt[:1000]},
                    ],
                },
            )
        if resp.status_code != 200:
            raise RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text[:200]}")

        body = resp.json()
        raw_content = body["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_json_fences(raw_content))
        if not isinstance(parsed, dict):
            raise ValueError("Respuesta LLM no es objeto JSON")

        intent = str(parsed.get("intent") or "").strip()
        if intent == "rechazado":
            _reject_disallowed_prompt()
        if intent not in WHITELIST_INTENTS:
            raise ValueError(f"Intent '{intent}' fuera de whitelist")

        params = _extract_common_params(prompt)
        mes_llm = parsed.get("mes")
        if isinstance(mes_llm, int) and 1 <= mes_llm <= 12 and "mes" not in params:
            year = datetime.now().year
            params["mes"] = mes_llm
            params["fecha_inicio"] = date(year, mes_llm, 1)
            next_m = mes_llm + 1 if mes_llm < 12 else 1
            next_y = year if mes_llm < 12 else year + 1
            params["fecha_fin"] = date(next_y, next_m, 1) - timedelta(days=1)

        lim_llm = parsed.get("limite")
        if isinstance(lim_llm, int) and 1 <= lim_llm <= 50:
            params["limite"] = lim_llm

        return intent, params, model
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Fallo adaptador LLM (%s), aplicando fallback regex BR-08", exc)
        intent, params = clasificar_intencion_whitelist(prompt)
        return intent, params, "whitelist-regex-fallback"


def clasificar_intencion_whitelist(prompt: str) -> Tuple[str, Dict[str, Any]]:
    """Clasifica la consulta en lenguaje natural contra la whitelist de reportes autorizados (BR-08)."""
    if _BLOCKED_SQL_PATTERNS.search(prompt or ""):
        _reject_disallowed_prompt()

    p_lower = prompt.lower().strip()

    # Extracción de parámetros comunes
    parametros: Dict[str, Any] = {}

    # Detección de meses
    meses_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    for mes_nombre, mes_num in meses_map.items():
        if mes_nombre in p_lower:
            year = datetime.now().year
            parametros["mes"] = mes_num
            parametros["mes_nombre"] = mes_nombre.capitalize()
            parametros["fecha_inicio"] = date(year, mes_num, 1)
            # Fin de mes
            next_month = mes_num + 1 if mes_num < 12 else 1
            next_year = year if mes_num < 12 else year + 1
            parametros["fecha_fin"] = date(next_year, next_month, 1) - timedelta(days=1)
            break

    # Detección de límites
    if "diez" in p_lower or "10" in p_lower:
        parametros["limite"] = 10
    elif "cinco" in p_lower or "5" in p_lower:
        parametros["limite"] = 5
    elif "veinte" in p_lower or "20" in p_lower:
        parametros["limite"] = 20
    else:
        parametros["limite"] = 10

    # Matching contra intents
    for intent, patterns in WHITELIST_INTENTS.items():
        for pat in patterns:
            if re.search(pat, p_lower):
                return intent, parametros

    # Fallback por defecto si menciona ventas o inventario
    if "venta" in p_lower or "vendido" in p_lower:
        return "ventas_por_sucursal", parametros
    if "stock" in p_lower or "inventario" in p_lower:
        return "rotacion_stock_critico", parametros

    _reject_disallowed_prompt()


async def procesar_reporte_ia(
    conn: Connection,
    empresa_id: UUID,
    usuario_id: UUID,
    payload: ReporteIaRequest,
) -> ReporteIaResponse:
    """CU-34: Procesa solicitud en lenguaje natural con LLM + whitelist y aislamiento por empresa_id."""
    await validar_plan_profesional(conn, empresa_id)

    consulta_id = uuid4()
    tiempo_inicio = datetime.now()

    try:
        tipo_reporte, params, modelo_usado = await clasificar_intencion_con_llm(payload.prompt)
    except HTTPException as exc:
        try:
            await conn.execute(
                """
                INSERT INTO consulta_ia_log (
                    id, empresa_id, usuario_id, prompt, respuesta, modelo_llm,
                    canal, reporte_tipo, parametros_json, latencia_ms, estado, ocurrido_en
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'rechazado_whitelist', '{}'::jsonb, 0, 'rechazado', now())
                """,
                consulta_id,
                empresa_id,
                usuario_id,
                payload.prompt,
                str(exc.detail),
                "whitelist-guard-br08",
                payload.canal,
            )
        except Exception as log_exc:
            logger.warning(f"No se pudo registrar rechazo en consulta_ia_log: {log_exc}")
        raise

    fecha_inicio = params.get("fecha_inicio", date.today() - timedelta(days=90))
    fecha_fin = params.get("fecha_fin", date.today())
    limite = params.get("limite", 10)

    # 1. Ejecución del reporte seguro según Whitelist
    if tipo_reporte == "ventas_por_sucursal":
        titulo = f"Ventas Consolidadas por Sucursal ({params.get('mes_nombre', 'Últimos 90 días')})"
        rows = await conn.fetch(
            """
            SELECT
                s.nombre AS sucursal,
                COUNT(v.id)::int AS total_operaciones,
                COALESCE(SUM(v.total), 0)::float AS monto_total,
                COALESCE(AVG(v.total), 0)::float AS ticket_promedio
            FROM sucursal s
            LEFT JOIN venta v ON v.sucursal_id = s.id 
                AND v.empresa_id = s.empresa_id 
                AND v.fecha_hora::date >= $2 
                AND v.fecha_hora::date <= $3
                AND v.estado IN ('pagada', 'completada', 'emitida')
            WHERE s.empresa_id = $1
            GROUP BY s.id, s.nombre
            ORDER BY monto_total DESC
            """,
            empresa_id,
            fecha_inicio,
            fecha_fin,
        )
        columnas = ["Sucursal", "Operaciones", "Monto Total (Bs.)", "Ticket Promedio (Bs.)"]
        filas = [
            {
                "sucursal": r["sucursal"],
                "operaciones": r["total_operaciones"],
                "monto_total": round(float(r["monto_total"]), 2),
                "ticket_promedio": round(float(r["ticket_promedio"]), 2),
            }
            for r in rows
        ]
        tipo_grafico = "barras"
        datos_grafico = {
            "labels": [f["sucursal"] for f in filas],
            "datasets": [
                {"label": "Ventas Totales (Bs.)", "data": [f["monto_total"] for f in filas]}
            ],
        }
        total_facturado = sum(f["monto_total"] for f in filas)
        sucursal_lider = filas[0]["sucursal"] if filas else "N/A"
        resumen_ejecutivo = (
            f"En el período analizado se consolidaron {sum(f['operaciones'] for f in filas)} transacciones "
            f"con una facturación total de Bs. {total_facturado:,.2f}. La sucursal con mayor volumen "
            f"comercial fue '{sucursal_lider}' representando el mayor aporte a los ingresos globales."
        )
        kpis = {
            "total_facturado_bs": round(total_facturado, 2),
            "sucursal_lider": sucursal_lider,
            "promedio_por_sucursal_bs": round(total_facturado / max(1, len(filas)), 2),
        }

    elif tipo_reporte == "top_productos_vendidos":
        titulo = f"Top {limite} Prendas Más Vendidas"
        rows = await conn.fetch(
            """
            SELECT
                p.codigo,
                p.nombre AS prenda,
                COALESCE(cat.nombre, 'Sin categoría') AS categoria,
                COALESCE(SUM(vd.cantidad), 0)::int AS unidades_vendidas,
                COALESCE(SUM(vd.subtotal), 0)::float AS total_recaudado
            FROM venta_detalle vd
            JOIN venta v ON v.id = vd.venta_id AND v.empresa_id = vd.empresa_id
            JOIN variante var ON var.id = vd.variante_id AND var.empresa_id = vd.empresa_id
            JOIN prenda p ON p.id = var.prenda_id AND p.empresa_id = vd.empresa_id
            LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
            WHERE vd.empresa_id = $1
              AND v.fecha_hora::date >= $2
              AND v.fecha_hora::date <= $3
              AND v.estado IN ('pagada', 'completada', 'emitida')
            GROUP BY p.codigo, p.nombre, cat.nombre
            ORDER BY unidades_vendidas DESC, total_recaudado DESC
            LIMIT $4
            """,
            empresa_id,
            fecha_inicio,
            fecha_fin,
            limite,
        )
        columnas = ["Código", "Prenda", "Categoría", "Unidades Vendidas", "Ingresos (Bs.)"]
        filas = [
            {
                "codigo": r["codigo"],
                "prenda": r["prenda"],
                "categoria": r["categoria"],
                "unidades_vendidas": r["unidades_vendidas"],
                "ingresos": round(float(r["total_recaudado"]), 2),
            }
            for r in rows
        ]
        tipo_grafico = "barras"
        datos_grafico = {
            "labels": [f["prenda"][:18] for f in filas],
            "datasets": [
                {"label": "Unidades", "data": [f["unidades_vendidas"] for f in filas]}
            ],
        }
        total_prendas = sum(f["unidades_vendidas"] for f in filas)
        resumen_ejecutivo = (
            f"El catálogo líder concentra {total_prendas} unidades comercializadas en el período. "
            f"La prenda más demandada fue '{filas[0]['prenda'] if filas else 'N/A'}' con "
            f"{filas[0]['unidades_vendidas'] if filas else 0} unidades despachadas."
        )
        kpis = {
            "unidades_totales_ranking": total_prendas,
            "prenda_estrella": filas[0]["prenda"] if filas else "N/A",
            "ingresos_top_prendas": round(sum(f["ingresos"] for f in filas), 2),
        }

    elif tipo_reporte == "ventas_temporales_semana":
        titulo = "Evolución y Tendencia Temporal de Ventas Semanales"
        rows = await conn.fetch(
            """
            SELECT
                to_char(date_trunc('week', fecha_hora), 'YYYY-"W"IW') AS semana,
                COUNT(id)::int AS operaciones,
                COALESCE(SUM(total), 0)::float AS total_semanal
            FROM venta
            WHERE empresa_id = $1 
              AND fecha_hora::date >= ($2::date - interval '12 weeks')
              AND estado IN ('pagada', 'completada', 'emitida')
            GROUP BY date_trunc('week', fecha_hora)
            ORDER BY date_trunc('week', fecha_hora) ASC
            """,
            empresa_id,
            fecha_fin,
        )
        columnas = ["Semana", "Operaciones", "Venta Total (Bs.)"]
        filas = [
            {
                "semana": r["semana"],
                "operaciones": r["operaciones"],
                "total_semanal": round(float(r["total_semanal"]), 2),
            }
            for r in rows
        ]
        tipo_grafico = "lineas"
        datos_grafico = {
            "labels": [f["semana"] for f in filas],
            "datasets": [
                {"label": "Ventas Semanales (Bs.)", "data": [f["total_semanal"] for f in filas]}
            ],
        }
        resumen_ejecutivo = (
            "Se observa la trayectoria de ventas durante las últimas 12 semanas operativas, "
            "permitiendo proyectar picos estacionales e índices de conversión sostenidos."
        )
        kpis = {
            "semanas_evaluadas": len(filas),
            "promedio_semanal_bs": round(
                sum(f["total_semanal"] for f in filas) / max(1, len(filas)), 2
            ),
        }

    elif tipo_reporte == "analisis_canales_pago":
        titulo = "Análisis de Ventas por Canal y Método de Pago"
        rows = await conn.fetch(
            """
            SELECT
                v.canal,
                COALESCE(p.metodo, 'sin_pago') AS metodo,
                COUNT(DISTINCT v.id)::int AS operaciones,
                COALESCE(SUM(COALESCE(p.monto, v.total)), 0)::float AS monto_total
            FROM venta v
            LEFT JOIN pago p ON p.venta_id = v.id AND p.empresa_id = v.empresa_id AND p.estado = 'completado'
            WHERE v.empresa_id = $1
              AND v.fecha_hora::date >= $2
              AND v.fecha_hora::date <= $3
              AND v.estado IN ('pagada', 'completada', 'entregada', 'enviada')
            GROUP BY v.canal, COALESCE(p.metodo, 'sin_pago')
            ORDER BY monto_total DESC
            """,
            empresa_id,
            fecha_inicio,
            fecha_fin,
        )
        columnas = ["Canal", "Método de Pago", "Operaciones", "Monto Total (Bs.)"]
        filas = [
            {
                "canal": r["canal"],
                "metodo": r["metodo"],
                "operaciones": r["operaciones"],
                "monto_total": round(float(r["monto_total"]), 2),
            }
            for r in rows
        ]
        tipo_grafico = "torta"
        datos_grafico = {
            "labels": [f"{f['canal']} - {f['metodo']}" for f in filas],
            "datasets": [
                {"label": "Recaudación por Canal/Método", "data": [f["monto_total"] for f in filas]}
            ],
        }
        total_canal = sum(f["monto_total"] for f in filas)
        resumen_ejecutivo = (
            f"Se consolidaron Bs. {total_canal:,.2f} a través de {len(filas)} combinaciones de canal y método de pago "
            f"en el período seleccionado."
        )
        kpis = {
            "total_recaudado_bs": round(total_canal, 2),
            "combinaciones_activas": len(filas),
        }

    else:  # rotacion_stock_critico
        titulo = "Alertas de Stock Crítico y Rotación de Prendas"
        rows = await conn.fetch(
            """
            SELECT
                p.codigo,
                p.nombre AS prenda,
                COALESCE(cat.nombre, 'Sin categoría') AS categoria,
                COALESCE(SUM(i.stock_disponible), 0)::int AS stock_disponible,
                COALESCE(SUM(vd.cantidad), 0)::int AS salidas_acumuladas
            FROM prenda p
            LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
            LEFT JOIN variante var ON var.prenda_id = p.id AND var.empresa_id = p.empresa_id
            LEFT JOIN inventario i ON i.variante_id = var.id AND i.empresa_id = p.empresa_id
            LEFT JOIN venta_detalle vd ON vd.variante_id = var.id AND vd.empresa_id = p.empresa_id
            WHERE p.empresa_id = $1
            GROUP BY p.codigo, p.nombre, cat.nombre
            HAVING COALESCE(SUM(i.stock_disponible), 0) < 10
            ORDER BY stock_disponible ASC, salidas_acumuladas DESC
            LIMIT 15
            """,
            empresa_id,
        )
        columnas = ["Código", "Prenda", "Categoría", "Stock Disponible", "Salidas"]
        filas = [
            {
                "codigo": r["codigo"],
                "prenda": r["prenda"],
                "categoria": r["categoria"],
                "stock_disponible": r["stock_disponible"],
                "salidas": r["salidas_acumuladas"],
            }
            for r in rows
        ]
        tipo_grafico = "barras"
        datos_grafico = {
            "labels": [f["prenda"][:15] for f in filas],
            "datasets": [
                {"label": "Stock Disponible", "data": [f["stock_disponible"] for f in filas]}
            ],
        }
        resumen_ejecutivo = (
            f"Se identificaron {len(filas)} prendas con stock por debajo del umbral de seguridad (menos de 10 unidades). "
            "Se aconseja generar órdenes de reposición para evitar quiebres de inventario."
        )
        kpis = {
            "prendas_en_riesgo": len(filas),
            "unidades_stock_critico": sum(f["stock_disponible"] for f in filas),
        }

    latencia_ms = int((datetime.now() - tiempo_inicio).total_seconds() * 1000)

    # 2. Registro en tabla particionada consulta_ia_log
    try:
        await conn.execute(
            """
            INSERT INTO consulta_ia_log (
                id, empresa_id, usuario_id, prompt, respuesta, modelo_llm,
                canal, reporte_tipo, parametros_json, latencia_ms, estado, ocurrido_en
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, 'exitoso', now())
            """,
            consulta_id,
            empresa_id,
            usuario_id,
            payload.prompt,
            resumen_ejecutivo,
            modelo_usado,
            payload.canal,
            tipo_reporte,
            json.dumps(params, default=str),
            latencia_ms,
        )
    except Exception as e:
        logger.warning(f"No se pudo registrar log particionado consulta_ia_log: {e}")

    sugerencias = [
        "¿Cuáles fueron los diez productos más vendidos este mes?",
        "Mostrame las ventas de septiembre agrupadas por sucursal",
        "Generá un gráfico de ventas por semana",
        "Rotación y stock crítico por categoría",
    ]

    return ReporteIaResponse(
        consulta_id=consulta_id,
        prompt_recibido=payload.prompt,
        tipo_reporte=tipo_reporte,
        titulo=titulo,
        resumen_ejecutivo=resumen_ejecutivo,
        kpis=kpis,
        columnas=columnas,
        filas=filas,
        tipo_grafico=tipo_grafico,
        datos_grafico=datos_grafico,
        parametros_aplicados=params,
        sugerencias=sugerencias,
        permitido_exportar=True,
    )


# ---------------------------------------------------------------------------
# Exportación Dinámica a Excel (.xlsx) y PDF (.pdf)
# ---------------------------------------------------------------------------

async def exportar_reporte(
    conn: Connection,
    empresa_id: UUID,
    usuario_id: UUID,
    payload: ExportarReporteRequest,
) -> ExportarReporteResponse:
    """CU-34: Ensambla y descarga binario dinámico en formato Microsoft Excel o PDF."""
    reporte_id = uuid4()
    formato = payload.formato.lower()
    nombre_archivo = f"reporte_{payload.tipo_reporte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{formato}"

    if formato == "xlsx":
        contenido_bytes = generar_excel(payload)
    elif formato == "pdf":
        contenido_bytes = generar_pdf(payload)
    else:
        # Fallback csv
        contenido_bytes = generar_csv(payload)

    tamano = len(contenido_bytes)
    contenido_b64 = base64.b64encode(contenido_bytes).decode("utf-8")
    archivo_url = f"/api/v1/reportes/descarga/{reporte_id}.{formato}"

    # Registro en reporte_exportado
    try:
        await conn.execute(
            """
            INSERT INTO reporte_exportado (
                id, empresa_id, usuario_id, tipo_reporte, formato,
                archivo_url, tamano_bytes, estado, generado_en
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'generado', now())
            """,
            reporte_id,
            empresa_id,
            usuario_id,
            payload.tipo_reporte,
            formato,
            archivo_url,
            tamano,
        )
    except Exception as e:
        logger.warning(f"No se pudo registrar en reporte_exportado: {e}")

    return ExportarReporteResponse(
        reporte_id=reporte_id,
        tipo_reporte=payload.tipo_reporte,
        formato=formato,
        archivo_url=archivo_url,
        tamano_bytes=tamano,
        generado_en=datetime.now(),
        contenido_base64=contenido_b64,
    )


def generar_excel(payload: ExportarReporteRequest) -> bytes:
    """Genera archivo .xlsx estructurado con estilos usando openpyxl."""
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Analítico"

    # Encabezado corporativo
    ws.merge_cells("A1:E1")
    title_cell = ws["A1"]
    title_cell.value = f"FASHION STORE SaaS - {payload.titulo.upper()}"
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    # Subtítulo y fecha
    ws.merge_cells("A2:E2")
    sub_cell = ws["A2"]
    sub_cell.value = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Resumen: {payload.resumen or ''}"
    sub_cell.font = Font(name="Calibri", size=9, italic=True, color="333333")
    sub_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 20

    # Fila de columnas
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    for col_idx, col_name in enumerate(payload.columnas, start=1):
        c = ws.cell(row=4, column=col_idx, value=col_name)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
    ws.row_dimensions[4].height = 26

    # Filas de datos
    for row_idx, fila in enumerate(payload.filas, start=5):
        ws.row_dimensions[row_idx].height = 20
        keys = list(fila.keys())
        for col_idx, val in enumerate(fila.values(), start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if isinstance(val, (int, float)):
                cell.alignment = Alignment(horizontal="right")
                if "monto" in keys[col_idx - 1] or "total" in keys[col_idx - 1] or "ingreso" in keys[col_idx - 1]:
                    cell.number_format = "#,##0.00"
            else:
                cell.alignment = Alignment(horizontal="left")

    # Ajuste automático de anchos
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generar_pdf(payload: ExportarReporteRequest) -> bytes:
    """Genera documento PDF corporativo con reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    elements = []

    # Título
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6,
    )
    elements.append(Paragraph(f"FashionStore SaaS - {payload.titulo}", title_style))

    # Meta
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=12,
    )
    fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Fecha de emisión: {fecha_str} | Tipo: {payload.tipo_reporte}", meta_style))

    if payload.resumen:
        resumen_style = ParagraphStyle(
            "ReportResumen",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=14,
        )
        elements.append(Paragraph(f"<b>Diagnóstico Ejecutivo:</b> {payload.resumen}", resumen_style))

    # Tabla de datos
    data = [payload.columnas]
    for fila in payload.filas:
        row_data = [str(v) for v in fila.values()]
        data.append(row_data)

    col_widths = [doc.width / max(1, len(payload.columnas))] * len(payload.columnas)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
            ]
        )
    )
    elements.append(t)

    doc.build(elements)
    return buf.getvalue()


def generar_csv(payload: ExportarReporteRequest) -> bytes:
    """Genera CSV delimitado por comas."""
    import csv

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(payload.columnas)
    for f in payload.filas:
        writer.writerow(list(f.values()))
    return output.getvalue().encode("utf-8")

