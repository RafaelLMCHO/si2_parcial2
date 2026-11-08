import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from asyncpg import Connection

from app.schemas.reportes import (
    DashboardConvencionalResponse,
    RotacionStockItem,
    RotacionStockResponse,
    TopPrendasItem,
    TopPrendasResponse,
    VentasPeriodoItem,
    VentasPeriodoResponse,
)

logger = logging.getLogger(__name__)


async def obtener_ventas_periodo(
    conn: Connection,
    empresa_id: UUID,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    sucursal_id: Optional[UUID] = None,
) -> VentasPeriodoResponse:
    """CU-33: Agrupa ventas consolidadas por día o mes con aislamiento estricto por empresa_id."""
    if not fecha_inicio:
        fecha_inicio = date.today() - timedelta(days=30)
    if not fecha_fin:
        fecha_fin = date.today()

    conditions = [
        "v.empresa_id = $1",
        "v.fecha_hora::date >= $2",
        "v.fecha_hora::date <= $3",
        "v.estado IN ('pagada', 'completada', 'entregada', 'enviada')",
    ]
    params: List[Any] = [empresa_id, fecha_inicio, fecha_fin]

    if sucursal_id:
        params.append(sucursal_id)
        conditions.append(f"v.sucursal_id = ${len(params)}")

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            to_char(v.fecha_hora, 'YYYY-MM-DD') AS periodo,
            COUNT(v.id) AS total_transacciones,
            COALESCE(SUM(v.total), 0)::float AS monto_total,
            COALESCE(AVG(v.total), 0)::float AS ticket_promedio
        FROM venta v
        WHERE {where_clause}
        GROUP BY to_char(v.fecha_hora, 'YYYY-MM-DD')
        ORDER BY periodo ASC
    """
    rows = await conn.fetch(sql, *params)

    items = [
        VentasPeriodoItem(
            periodo=r["periodo"],
            total_transacciones=int(r["total_transacciones"]),
            monto_total=float(r["monto_total"]),
            ticket_promedio=round(float(r["ticket_promedio"]), 2),
        )
        for r in rows
    ]

    total_general = sum(item.monto_total for item in items)
    total_operaciones = sum(item.total_transacciones for item in items)
    ticket_promedio_general = (
        round(total_general / total_operaciones, 2) if total_operaciones > 0 else 0.0
    )

    return VentasPeriodoResponse(
        items=items,
        total_general=round(total_general, 2),
        total_operaciones=total_operaciones,
        ticket_promedio_general=ticket_promedio_general,
    )


async def obtener_rotacion_stock(
    conn: Connection,
    empresa_id: UUID,
    categoria_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
) -> RotacionStockResponse:
    """CU-33: Calcula entradas, salidas y ratio de rotación del inventario por prenda."""
    conditions = ["p.empresa_id = $1"]
    params: List[Any] = [empresa_id]

    if categoria_id:
        params.append(categoria_id)
        conditions.append(f"p.categoria_id = ${len(params)}")

    where_clause = " AND ".join(conditions)

    sucursal_filter = ""
    if sucursal_id:
        params.append(sucursal_id)
        sucursal_filter = f"AND i.sucursal_id = ${len(params)}"

    sql = f"""
        WITH stock AS (
            SELECT var.prenda_id, COALESCE(SUM(i.stock_disponible), 0)::int AS stock_actual
            FROM variante var
            JOIN inventario i ON i.variante_id = var.id AND i.empresa_id = var.empresa_id
            WHERE var.empresa_id = $1 {sucursal_filter}
            GROUP BY var.prenda_id
        ),
        salidas AS (
            SELECT var.prenda_id, COALESCE(SUM(vd.cantidad), 0)::int AS salidas
            FROM venta_detalle vd
            JOIN variante var ON var.id = vd.variante_id AND var.empresa_id = vd.empresa_id
            WHERE vd.empresa_id = $1
            GROUP BY var.prenda_id
        )
        SELECT
            p.id AS prenda_id,
            p.codigo,
            p.nombre,
            COALESCE(cat.nombre, 'Sin categoría') AS categoria,
            COALESCE(st.stock_actual, 0)::int AS stock_actual,
            COALESCE(sa.salidas, 0)::int AS salidas
        FROM prenda p
        LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
        LEFT JOIN stock st ON st.prenda_id = p.id
        LEFT JOIN salidas sa ON sa.prenda_id = p.id
        WHERE {where_clause}
        ORDER BY salidas DESC, stock_actual ASC
        LIMIT 50
    """
    rows = await conn.fetch(sql, *params)

    items: List[RotacionStockItem] = []
    criticos = 0
    total_unidades = 0

    for r in rows:
        stock = int(r["stock_actual"])
        salidas = int(r["salidas"])
        entradas = stock + salidas  # estimación base
        total_unidades += stock
        ratio = round(salidas / max(1, stock + salidas), 2)
        alerta = stock < 5
        if alerta:
            criticos += 1

        items.append(
            RotacionStockItem(
                prenda_id=r["prenda_id"],
                codigo=r["codigo"],
                nombre=r["nombre"],
                categoria=r["categoria"],
                stock_actual=stock,
                entradas=entradas,
                salidas=salidas,
                rotacion_ratio=ratio,
                alerta_stock=alerta,
            )
        )

    return RotacionStockResponse(
        items=items,
        prendas_stock_critico=criticos,
        stock_total_unidades=total_unidades,
    )


async def obtener_top_prendas(
    conn: Connection,
    empresa_id: UUID,
    limite: int = 10,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
) -> TopPrendasResponse:
    """CU-33: Obtiene el ranking de prendas más vendidas por cantidad e ingresos."""
    if not fecha_inicio:
        fecha_inicio = date.today() - timedelta(days=90)
    if not fecha_fin:
        fecha_fin = date.today()

    sql = """
        SELECT
            p.id AS prenda_id,
            p.codigo,
            p.nombre,
            COALESCE(cat.nombre, 'General') AS categoria,
            COALESCE(SUM(vd.cantidad), 0)::int AS cantidad_vendida,
            COALESCE(SUM(vd.subtotal), 0)::float AS total_ingresos
        FROM venta_detalle vd
        JOIN venta v ON v.id = vd.venta_id AND v.empresa_id = vd.empresa_id
        JOIN variante var ON var.id = vd.variante_id AND var.empresa_id = vd.empresa_id
        JOIN prenda p ON p.id = var.prenda_id AND p.empresa_id = vd.empresa_id
        LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
        WHERE vd.empresa_id = $1
          AND v.fecha_hora::date >= $2
          AND v.fecha_hora::date <= $3
          AND v.estado IN ('pagada', 'completada', 'emitida')
        GROUP BY p.id, p.codigo, p.nombre, cat.nombre
        ORDER BY cantidad_vendida DESC, total_ingresos DESC
        LIMIT $4
    """
    rows = await conn.fetch(sql, empresa_id, fecha_inicio, fecha_fin, limite)

    items = [
        TopPrendasItem(
            ranking=idx + 1,
            prenda_id=r["prenda_id"],
            codigo=r["codigo"],
            nombre=r["nombre"],
            categoria=r["categoria"],
            cantidad_vendida=int(r["cantidad_vendida"]),
            total_ingresos=round(float(r["total_ingresos"]), 2),
        )
        for idx, r in enumerate(rows)
    ]

    total_vendidas = sum(i.cantidad_vendida for i in items)
    total_ingresos = sum(i.total_ingresos for i in items)

    return TopPrendasResponse(
        items=items,
        total_prendas_vendidas=total_vendidas,
        total_ingresos_generados=round(total_ingresos, 2),
    )


async def obtener_dashboard_convencional(
    conn: Connection,
    empresa_id: UUID,
) -> DashboardConvencionalResponse:
    """CU-33: Tablero consolidado para planes Básico y Profesional con KPIs y tendencias."""
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    # 1. Ventas hoy
    monto_hoy = await conn.fetchval(
        """
        SELECT COALESCE(SUM(total), 0)::float
        FROM venta
        WHERE empresa_id = $1 AND fecha_hora::date = $2 AND estado IN ('pagada', 'completada', 'emitida')
        """,
        empresa_id,
        hoy,
    )

    # 2. Ventas mes
    monto_mes = await conn.fetchval(
        """
        SELECT COALESCE(SUM(total), 0)::float
        FROM venta
        WHERE empresa_id = $1 AND fecha_hora::date >= $2 AND estado IN ('pagada', 'completada', 'emitida')
        """,
        empresa_id,
        inicio_mes,
    )

    # 3. Stock total
    stock_total = await conn.fetchval(
        """
        SELECT COALESCE(SUM(stock_actual), 0)::int
        FROM inventario
        WHERE empresa_id = $1
        """,
        empresa_id,
    )

    # 4. Reservas activas
    reservas_activas = await conn.fetchval(
        """
        SELECT COUNT(id)::int
        FROM reserva
        WHERE empresa_id = $1 AND estado IN ('confirmada', 'en_preparacion', 'lista_para_retiro')
        """,
        empresa_id,
    )

    # 5. Ventas por sucursal
    sucursales_rows = await conn.fetch(
        """
        SELECT
            s.id AS sucursal_id,
            s.nombre AS sucursal_nombre,
            COALESCE(SUM(v.total), 0)::float AS total_ventas,
            COUNT(v.id)::int AS operaciones
        FROM sucursal s
        LEFT JOIN venta v ON v.sucursal_id = s.id AND v.empresa_id = s.empresa_id AND v.estado IN ('pagada', 'completada', 'emitida')
        WHERE s.empresa_id = $1
        GROUP BY s.id, s.nombre
        ORDER BY total_ventas DESC
        """,
        empresa_id,
    )

    ventas_sucursal = [
        {
            "sucursal_id": str(r["sucursal_id"]),
            "sucursal_nombre": r["sucursal_nombre"],
            "total_ventas": round(float(r["total_ventas"]), 2),
            "operaciones": int(r["operaciones"]),
        }
        for r in sucursales_rows
    ]

    # 6. Tendencia últimos 7 días
    tendencia_rows = await conn.fetch(
        """
        SELECT
            to_char(d.dia, 'YYYY-MM-DD') AS fecha,
            COALESCE(SUM(v.total), 0)::float AS total
        FROM generate_series($2::date - interval '6 days', $2::date, '1 day'::interval) d(dia)
        LEFT JOIN venta v ON v.fecha_hora::date = d.dia::date AND v.empresa_id = $1 AND v.estado IN ('pagada', 'completada', 'emitida')
        GROUP BY d.dia
        ORDER BY d.dia ASC
        """,
        empresa_id,
        hoy,
    )

    tendencias = [
        {"fecha": r["fecha"], "total": round(float(r["total"]), 2)}
        for r in tendencia_rows
    ]

    top_prendas = await obtener_top_prendas(conn, empresa_id, limite=5)
    rotacion = await obtener_rotacion_stock(conn, empresa_id)

    return DashboardConvencionalResponse(
        kpis={
            "ventas_hoy": round(float(monto_hoy or 0), 2),
            "ventas_mes": round(float(monto_mes or 0), 2),
            "stock_total_unidades": int(stock_total or 0),
            "reservas_activas": int(reservas_activas or 0),
        },
        ventas_por_sucursal=ventas_sucursal,
        top_prendas=top_prendas.items,
        rotacion_resumen={
            "stock_critico": rotacion.prendas_stock_critico,
            "total_unidades": rotacion.stock_total_unidades,
        },
        ventas_tendencia_dias=tendencias,
    )

