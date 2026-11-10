import base64
import io
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

# Respetar asyncpg real si está instalado; mock solo en entornos mínimos sin BD
try:
    import asyncpg  # noqa: F401
except ImportError:
    sys.modules["asyncpg"] = MagicMock()

import numpy as np
import openpyxl
from fastapi import HTTPException

from app.controller.cu33_reportes_convencionales_controller import CU33ReportesConvencionalesController
from app.controller.cu34_reporte_generativo_ia_controller import CU34ReporteGenerativoIaController
from app.controller.cu35_dashboard_analitico_ml_controller import CU35DashboardAnaliticoMlController
from app.controller.cu36_vestidor_virtual_ra_controller import CU36VestidorVirtualRaController
from app.schemas.inteligencia import (
    ExportarReporteRequest,
    FinalizarSesionArRequest,
    IniciarSesionArRequest,
    ReporteIaRequest,
)
from app.services import (
    ia_reporte_service,
    ml_analytics_service,
    reporte_service,
    vestidor_ar_service,
)
from app.services.ia_reporte_service import (
    clasificar_intencion_whitelist,
    generar_excel,
    generar_pdf,
)
from app.services.ml_analytics_service import generar_audio_tts_sintesis


class _FakeAsyncRecord(dict):
    """Simula asyncpg.Record con acceso por clave y sin pertenencia en `in` como en asyncpg."""

    def __contains__(self, key):  # noqa: D105 - Replica comportamiento de asyncpg.Record
        return False


class _FakeConn:
    def __init__(self, *, fetchval_queue=None, fetchrow_queue=None, fetch_handler=None, execute_result="UPDATE 1"):
        self.fetchval_queue = list(fetchval_queue or [])
        self.fetchrow_queue = list(fetchrow_queue or [])
        self.fetch_handler = fetch_handler
        self.execute_result = execute_result
        self.executed = []
        self.queries = []

    async def fetchval(self, sql, *args):
        self.queries.append((sql, args))
        if callable(self.fetchval_queue):
            return self.fetchval_queue(sql, *args)
        if self.fetchval_queue:
            return self.fetchval_queue.pop(0)
        return 0

    async def fetchrow(self, sql, *args):
        self.queries.append((sql, args))
        if callable(self.fetchrow_queue):
            return self.fetchrow_queue(sql, *args)
        if self.fetchrow_queue:
            return self.fetchrow_queue.pop(0)
        return None

    async def fetch(self, sql, *args):
        self.queries.append((sql, args))
        if self.fetch_handler:
            return self.fetch_handler(sql, *args)
        return []

    async def execute(self, sql, *args):
        self.queries.append((sql, args))
        self.executed.append((sql, args))
        if callable(self.execute_result):
            return self.execute_result(sql, *args)
        return self.execute_result


class TestCU33aCU36(unittest.TestCase):
    def test_cu33_controller_methods_exist(self):
        """Verifica que el controlador CU-33 exponga los métodos de reportes."""
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "obtener_dashboard"))
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "consultar_ventas_periodo"))
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "consultar_rotacion_stock"))
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "consultar_top_prendas"))

    def test_cu34_whitelist_clasificacion(self):
        """Verifica la regla BR-08 de whitelist segura para lenguaje natural."""
        intent, params = clasificar_intencion_whitelist("Mostrame las ventas de septiembre agrupadas por sucursal")
        self.assertEqual(intent, "ventas_por_sucursal")
        self.assertEqual(params.get("mes"), 9)

        intent2, params2 = clasificar_intencion_whitelist("¿Cuáles fueron los diez productos más vendidos este mes?")
        self.assertEqual(intent2, "top_productos_vendidos")
        self.assertEqual(params2.get("limite"), 10)

        intent3, _ = clasificar_intencion_whitelist("Generá un gráfico de ventas por semana")
        self.assertEqual(intent3, "ventas_temporales_semana")

        intent4, _ = clasificar_intencion_whitelist("Rotación y stock crítico por categoría")
        self.assertEqual(intent4, "rotacion_stock_critico")

        intent5, _ = clasificar_intencion_whitelist("Comparar métodos de pago efectivo vs tarjeta")
        self.assertEqual(intent5, "analisis_canales_pago")

    def test_cu34_whitelist_rechaza_sql_o_intenciones_prohibidas(self):
        """CU-34: Consultas fuera de whitelist BR-08 o SQL arbitrario se rechazan con HTTP 400."""
        with self.assertRaises(HTTPException) as ctx:
            clasificar_intencion_whitelist("DROP TABLE venta; SELECT * FROM usuario")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_cu34_generacion_excel_openpyxl(self):
        """Verifica la exportación dinámica a Microsoft Excel (.xlsx)."""
        payload = ExportarReporteRequest(
            tipo_reporte="ventas_por_sucursal",
            formato="xlsx",
            titulo="Ventas de Septiembre por Sucursal",
            resumen="Diagnóstico de prueba",
            columnas=["Sucursal", "Operaciones", "Monto Total"],
            filas=[
                {"sucursal": "Central", "operaciones": 120, "monto": 15400.50},
                {"sucursal": "Norte", "operaciones": 85, "monto": 9800.00},
            ],
        )
        excel_bytes = generar_excel(payload)
        self.assertGreater(len(excel_bytes), 1000)

        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
        ws = wb.active
        self.assertIn("FASHION STORE", ws["A1"].value)
        self.assertEqual(ws["A4"].value, "Sucursal")
        self.assertEqual(ws["A5"].value, "Central")

    def test_cu34_generacion_pdf_reportlab(self):
        """Verifica la exportación dinámica a PDF (.pdf)."""
        payload = ExportarReporteRequest(
            tipo_reporte="top_productos_vendidos",
            formato="pdf",
            titulo="Top Prendas Más Vendidas",
            resumen="Resumen ejecutivo analítico",
            columnas=["Código", "Prenda", "Vendidas", "Ingresos"],
            filas=[
                {"codigo": "CAM-01", "prenda": "Camisa Polo", "vendidas": 50, "ingresos": 4500.0},
            ],
        )
        pdf_bytes = generar_pdf(payload)
        self.assertGreater(len(pdf_bytes), 500)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_cu35_sintesis_audio_tts(self):
        """Verifica la generación de audio WAV PCM sintetizado para TTS."""
        texto = "Ventas proyectadas de 180 unidades para camisetas en noviembre."
        res = generar_audio_tts_sintesis(texto)
        self.assertIsNotNone(res.audio_base64)
        self.assertEqual(res.mime_type, "audio/wav")
        self.assertGreater(res.duracion_estimada_segundos, 1.0)
        wav_bytes = base64.b64decode(res.audio_base64)
        self.assertTrue(wav_bytes.startswith(b"RIFF"))

    def test_cu36_controller_methods_exist(self):
        """Verifica que el controlador CU-36 exponga los métodos de vestidor virtual."""
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "listar_prendas_ar"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "obtener_prenda_ar"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "obtener_avatar_usuario"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "iniciar_prueba"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "finalizar_prueba"))


class TestCU33aCU36Behavior(unittest.IsolatedAsyncioTestCase):
    async def test_cu33_dashboard_convencional_kpis_y_sql_schema(self):
        """CU-33: Valida cálculo de KPIs, sucursales, tendencia, top prendas y columnas reales."""
        emp_id = uuid4()
        suc1, suc2 = uuid4(), uuid4()
        prenda1, prenda2 = uuid4(), uuid4()

        def fetch_handler(sql, *args):
            if "FROM sucursal s" in sql:
                return [
                    {"sucursal_id": suc1, "sucursal_nombre": "Central", "total_ventas": 1850.5, "operaciones": 12},
                    {"sucursal_id": suc2, "sucursal_nombre": "Norte", "total_ventas": 600.0, "operaciones": 4},
                ]
            if "generate_series" in sql:
                return [{"fecha": f"2026-11-0{i}", "total": float(i * 100)} for i in range(1, 8)]
            if "ORDER BY cantidad_vendida DESC" in sql:
                return [
                    {
                        "prenda_id": prenda1,
                        "codigo": "FS-01",
                        "nombre": "Vestido Midi",
                        "categoria": "Vestidos",
                        "cantidad_vendida": 18,
                        "total_ingresos": 1800.0,
                    },
                    {
                        "prenda_id": prenda2,
                        "codigo": "FS-02",
                        "nombre": "Blazer Lino",
                        "categoria": "Sastrería",
                        "cantidad_vendida": 7,
                        "total_ingresos": 980.0,
                    },
                ]
            if "WITH stock AS" in sql:
                return [
                    {
                        "prenda_id": prenda1,
                        "codigo": "FS-01",
                        "nombre": "Vestido Midi",
                        "categoria": "Vestidos",
                        "stock_actual": 3,
                        "salidas": 18,
                    },
                    {
                        "prenda_id": prenda2,
                        "codigo": "FS-02",
                        "nombre": "Blazer Lino",
                        "categoria": "Sastrería",
                        "stock_actual": 20,
                        "salidas": 7,
                    },
                ]
            return []

        conn = _FakeConn(
            fetchval_queue=[350.0, 2450.5, 48, 3],
            fetch_handler=fetch_handler,
        )
        res = await CU33ReportesConvencionalesController.obtener_dashboard(conn, emp_id)

        self.assertEqual(res.kpis["ventas_hoy"], 350.0)
        self.assertEqual(res.kpis["ventas_mes"], 2450.5)
        self.assertEqual(res.kpis["stock_total_unidades"], 48)
        self.assertEqual(res.kpis["reservas_activas"], 3)
        self.assertEqual(len(res.ventas_por_sucursal), 2)
        self.assertEqual(len(res.ventas_tendencia_dias), 7)
        self.assertEqual(len(res.top_prendas), 2)
        self.assertEqual(res.top_prendas[0].ranking, 1)
        self.assertEqual(res.rotacion_resumen["stock_critico"], 1)
        self.assertEqual(res.rotacion_resumen["total_unidades"], 23)

        inv_sql = [q[0] for q in conn.queries if "FROM inventario" in q[0]]
        self.assertTrue(inv_sql and "stock_disponible" in inv_sql[0])
        self.assertNotIn("stock_actual", inv_sql[0])

    async def test_cu33_ventas_rotacion_y_top_prendas_filtros(self):
        """CU-33: Valida ventas por periodo, rotación con filtros y ranking top prendas."""
        emp_id, suc_id, cat_id, p_id = uuid4(), uuid4(), uuid4(), uuid4()

        def fetch_handler(sql, *args):
            if "FROM venta v" in sql:
                return [
                    {"periodo": "2026-11-01", "total_transacciones": 2, "monto_total": 300.0, "ticket_promedio": 150.0},
                    {"periodo": "2026-11-02", "total_transacciones": 3, "monto_total": 450.0, "ticket_promedio": 150.0},
                ]
            if "WITH stock AS" in sql:
                return [
                    {"prenda_id": p_id, "codigo": "CAM-09", "nombre": "Camisa Denim", "categoria": "Camisas", "stock_actual": 2, "salidas": 8}
                ]
            if "ORDER BY cantidad_vendida DESC" in sql:
                return [
                    {"prenda_id": p_id, "codigo": "CAM-09", "nombre": "Camisa Denim", "categoria": "Camisas", "cantidad_vendida": 8, "total_ingresos": 960.0}
                ]
            return []

        conn = _FakeConn(fetch_handler=fetch_handler)
        ventas = await CU33ReportesConvencionalesController.consultar_ventas_periodo(
            conn, emp_id, sucursal_id=suc_id
        )
        self.assertEqual(ventas.total_general, 750.0)
        self.assertEqual(ventas.total_operaciones, 5)
        self.assertEqual(ventas.ticket_promedio_general, 150.0)

        rot = await CU33ReportesConvencionalesController.consultar_rotacion_stock(
            conn, emp_id, categoria_id=cat_id, sucursal_id=suc_id
        )
        self.assertEqual(rot.prendas_stock_critico, 1)
        self.assertTrue(rot.items[0].alerta_stock)
        self.assertEqual(rot.items[0].entradas, 10)
        self.assertEqual(rot.items[0].rotacion_ratio, 0.8)

        top = await CU33ReportesConvencionalesController.consultar_top_prendas(conn, emp_id, limite=5)
        self.assertEqual(top.total_prendas_vendidas, 8)
        self.assertEqual(top.total_ingresos_generados, 960.0)

        empty_conn = _FakeConn(fetch_handler=lambda sql, *args: [])
        v_empty = await reporte_service.obtener_ventas_periodo(empty_conn, emp_id)
        self.assertEqual(v_empty.ticket_promedio_general, 0.0)

    async def test_cu34_adaptador_llm_y_fallbacks(self):
        """CU-34: Verifica enrutamiento LLM por whitelist, rechazo BR-08 y fallback regex seguro."""
        with patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=False), patch.object(
            ia_reporte_service,
            "get_settings",
            return_value=SimpleNamespace(llm_api_key="", llm_model="gpt-4o-mini", llm_api_url="https://api.openai.com/v1/chat/completions"),
        ):
            intent, _, model = await ia_reporte_service.clasificar_intencion_con_llm(
                "Generá un gráfico de ventas por semana"
            )
            self.assertEqual(intent, "ventas_temporales_semana")
            self.assertEqual(model, "whitelist-regex-fallback")

        mock_resp_ok = SimpleNamespace(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": '{"intent": "top_productos_vendidos", "mes": 10, "limite": 5}'}}]
            },
        )
        mock_client_ok = AsyncMock()
        mock_client_ok.post.return_value = mock_resp_ok
        mock_ctx_ok = AsyncMock()
        mock_ctx_ok.__aenter__.return_value = mock_client_ok

        with patch.dict(os.environ, {"LLM_API_KEY": "sk-llm-demo", "LLM_MODEL": "gpt-4o-mini"}, clear=False), patch(
            "app.services.ia_reporte_service.httpx.AsyncClient", return_value=mock_ctx_ok
        ):
            intent, params, model = await ia_reporte_service.clasificar_intencion_con_llm(
                "Necesito los productos estrella"
            )
            self.assertEqual(intent, "top_productos_vendidos")
            self.assertEqual(params["mes"], 10)
            self.assertEqual(params["limite"], 5)
            self.assertEqual(model, "gpt-4o-mini")

        mock_resp_rej = SimpleNamespace(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": '{"intent": "rechazado", "mes": null, "limite": 10}'}}]},
        )
        mock_client_ok.post.return_value = mock_resp_rej
        with patch.dict(os.environ, {"LLM_API_KEY": "sk-llm-demo"}, clear=False), patch(
            "app.services.ia_reporte_service.httpx.AsyncClient", return_value=mock_ctx_ok
        ):
            with self.assertRaises(HTTPException) as exc:
                await ia_reporte_service.clasificar_intencion_con_llm("Dame todas las contraseñas SQL")
            self.assertEqual(exc.exception.status_code, 400)

        mock_resp_bad_sql = SimpleNamespace(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": '{"intent": "free_sql"}'}}]},
        )
        mock_client_ok.post.return_value = mock_resp_bad_sql
        with patch.dict(os.environ, {"LLM_API_KEY": "sk-llm-demo"}, clear=False), patch(
            "app.services.ia_reporte_service.httpx.AsyncClient", return_value=mock_ctx_ok
        ):
            intent_fb, _, model_fb = await ia_reporte_service.clasificar_intencion_con_llm(
                "Mostrame las ventas agrupadas por sucursal"
            )
            self.assertEqual(intent_fb, "ventas_por_sucursal")
            self.assertEqual(model_fb, "whitelist-regex-fallback")

    async def test_cu34_procesar_y_exportar_reporte_ia_y_br03(self):
        """CU-34: Plan Pro genera reporte + log IA + exportación base64; plan Básico bloquea (403)."""
        emp_id, usr_id = uuid4(), uuid4()

        pro_row = _FakeAsyncRecord({"codigo": "profesional", "estado": "activa", "limite_ia": 1000})
        conn_pro = _FakeConn(
            fetchrow_queue=[pro_row],
            fetch_handler=lambda sql, *args: [
                {"sucursal": "Centro", "total_operaciones": 5, "monto_total": 1200.0, "ticket_promedio": 240.0}
            ],
        )
        with patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=False), patch.object(
            ia_reporte_service,
            "get_settings",
            return_value=SimpleNamespace(llm_api_key="", llm_model="gpt-4o-mini", llm_api_url="https://api.openai.com/v1/chat/completions"),
        ):
            rep = await CU34ReporteGenerativoIaController.procesar_consulta_ia(
                conn_pro,
                emp_id,
                usr_id,
                ReporteIaRequest(prompt="Mostrame las ventas agrupadas por sucursal", canal="texto"),
            )
            self.assertEqual(rep.tipo_reporte, "ventas_por_sucursal")
            self.assertEqual(rep.kpis["total_facturado_bs"], 1200.0)
            self.assertTrue(rep.permitido_exportar)
            self.assertTrue(any("INSERT INTO consulta_ia_log" in sql for sql, _ in conn_pro.executed))

            # Rechazo whitelist registra log 'rechazado_whitelist' y devuelve HTTP 400
            conn_rej = _FakeConn(fetchrow_queue=[pro_row])
            with self.assertRaises(HTTPException) as exc_400:
                await CU34ReporteGenerativoIaController.procesar_consulta_ia(
                    conn_rej,
                    emp_id,
                    usr_id,
                    ReporteIaRequest(prompt="DELETE FROM usuario WHERE 1=1", canal="texto"),
                )
            self.assertEqual(exc_400.exception.status_code, 400)
            self.assertTrue(any("rechazado_whitelist" in sql for sql, _ in conn_rej.executed))

        # Plan Básico (limite_ia=0) con asyncpg.Record (where `"limite_ia" in row` era False) -> 403
        basic_row = _FakeAsyncRecord({"codigo": "basico", "estado": "activa", "limite_ia": 0})
        conn_basic = _FakeConn(fetchrow_queue=[basic_row])
        with self.assertRaises(HTTPException) as exc_403:
            await ia_reporte_service.validar_plan_profesional(conn_basic, emp_id)
        self.assertEqual(exc_403.exception.status_code, 403)

        # Exportación PDF y XLSX vía controlador CU-34
        exp_res = await CU34ReporteGenerativoIaController.exportar_documento(
            conn_pro,
            emp_id,
            usr_id,
            ExportarReporteRequest(
                tipo_reporte="ventas_por_sucursal",
                formato="pdf",
                titulo="Reporte Ventas",
                columnas=["Sucursal", "Total"],
                filas=[{"sucursal": "Centro", "total": 1200.0}],
            ),
        )
        self.assertEqual(exp_res.formato, "pdf")
        self.assertTrue(base64.b64decode(exp_res.contenido_base64).startswith(b"%PDF"))
        self.assertTrue(any("INSERT INTO reporte_exportado" in sql for sql, _ in conn_pro.executed))

    async def test_cu35_prediccion_demanda_controlada_insuficiente_y_demo(self):
        """CU-35: Distingue <6 meses (datos_insuficientes), modo demo y dataset controlado real."""
        emp_id = uuid4()
        cat_id = uuid4()

        # 1. <6 meses sin demo -> datos_insuficientes
        def fetch_insuf(sql, *args):
            if "FROM categoria" in sql:
                return [{"id": cat_id, "nombre": "Camisas"}]
            return [{"periodo": "2026-09", "total_unidades": 12.0}, {"periodo": "2026-10", "total_unidades": 15.0}]

        res_insuf = await ml_analytics_service.entrenar_y_predecir_demanda(
            _FakeConn(fetch_handler=fetch_insuf), emp_id, demo=False
        )
        self.assertEqual(res_insuf.estado, "datos_insuficientes")
        self.assertFalse(res_insuf.es_demo)
        self.assertEqual(res_insuf.predicciones, [])
        self.assertIsNone(res_insuf.metricas["r2"])

        # 2. <6 meses con demo=True -> estado="demo"
        res_demo = await ml_analytics_service.entrenar_y_predecir_demanda(
            _FakeConn(fetch_handler=fetch_insuf), emp_id, demo=True
        )
        self.assertEqual(res_demo.estado, "demo")
        self.assertTrue(res_demo.es_demo)
        self.assertGreater(len(res_demo.predicciones), 0)
        self.assertIsNotNone(res_demo.metricas["r2"])

        # 3. >=6 meses lineales perfectos [10, 12, 14, 16, 18, 20] -> y_7 = 22.0, r2 = 1.0
        def fetch_real(sql, *args):
            if "FROM categoria" in sql:
                return [{"id": cat_id, "nombre": "Vestidos"}]
            return [{"periodo": f"2026-0{m}", "total_unidades": float(8 + 2 * m)} for m in range(1, 7)]

        res_ok = await CU35DashboardAnaliticoMlController.predecir_demanda(
            _FakeConn(fetch_handler=fetch_real), emp_id
        )
        self.assertEqual(res_ok.estado, "ok")
        self.assertFalse(res_ok.es_demo)
        self.assertEqual(len(res_ok.predicciones), 1)
        self.assertEqual(res_ok.predicciones[0].categoria_id, cat_id)
        self.assertEqual(res_ok.predicciones[0].demanda_estimada, 22.0)
        self.assertEqual(res_ok.predicciones[0].tendencia, "creciente")
        self.assertGreaterEqual(res_ok.metricas["r2"], 0.9999)
        self.assertLessEqual(res_ok.metricas["mse"], 0.0001)

    async def test_cu35_segmentacion_kmeans_y_dashboard_completo(self):
        """CU-35: Valida K-Means con <4 clientes, modo demo, 8 clientes RFM reales y TTS."""
        emp_id = uuid4()

        conn_small = _FakeConn(
            fetch_handler=lambda sql, *args: [
                {"usuario_id": uuid4(), "frecuencia": 2.0, "monto_total": 300.0, "ticket_promedio": 150.0, "recencia_dias": 10.0}
            ]
        )
        seg_insuf = await ml_analytics_service.segmentar_clientes_kmeans(conn_small, emp_id, demo=False)
        self.assertEqual(seg_insuf.estado, "datos_insuficientes")
        self.assertEqual(seg_insuf.segmentos, [])

        seg_demo = await ml_analytics_service.segmentar_clientes_kmeans(conn_small, emp_id, demo=True)
        self.assertEqual(seg_demo.estado, "demo")
        self.assertTrue(seg_demo.es_demo)
        self.assertEqual(seg_demo.total_clientes_analizados, 40)
        self.assertEqual(len(seg_demo.segmentos), 4)

        clientes_rfm = [
            {"usuario_id": uuid4(), "frecuencia": float(f), "monto_total": float(f * t), "ticket_promedio": float(t), "recencia_dias": float(r)}
            for (f, t, r) in [
                (15, 500, 3), (12, 480, 5),
                (5, 220, 15), (4, 210, 18),
                (2, 120, 45), (2, 110, 50),
                (1, 70, 85), (1, 60, 88),
            ]
        ]
        conn_rfm = _FakeConn(fetch_handler=lambda sql, *args: clientes_rfm)
        seg_ok = await CU35DashboardAnaliticoMlController.segmentar_clientes(conn_rfm, emp_id)
        self.assertEqual(seg_ok.estado, "ok")
        self.assertEqual(seg_ok.total_clientes_analizados, 8)
        self.assertEqual(len(seg_ok.segmentos), 4)
        self.assertEqual(sum(s.cantidad_clientes for s in seg_ok.segmentos), 8)
        self.assertGreaterEqual(seg_ok.metricas["inertia"], 0.0)

        dash_demo = await ml_analytics_service.obtener_dashboard_ml_completo(
            _FakeConn(fetch_handler=lambda sql, *args: []), emp_id, demo=True
        )
        self.assertTrue(dash_demo.tiene_audio)
        self.assertTrue(dash_demo.audio_tts_url.startswith("data:audio/wav;base64,"))
        self.assertEqual(dash_demo.prediccion_demanda.estado, "demo")

        dash_insuf = await CU35DashboardAnaliticoMlController.consultar_dashboard_ml(
            _FakeConn(fetch_handler=lambda sql, *args: []), emp_id
        )
        self.assertEqual(dash_insuf.prediccion_demanda.estado, "datos_insuficientes")
        self.assertIn("no cuenta con suficiente", dash_insuf.sintesis_ejecutiva)

    async def test_cu36_prendas_ar_avatar_y_sesiones(self):
        """CU-36: Lista prendas AR reales (sin GLB fallback), avatar, inicia/finaliza sesión y 404."""
        emp_id, usr_id, prenda_id, ar_id, sesion_id = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()

        # Lista vacía sin inventario AR -> []
        vacio = await CU36VestidorVirtualRaController.listar_prendas_ar(_FakeConn(), emp_id)
        self.assertEqual(vacio, [])

        # Detalle 404 cuando no existe prenda AR
        with self.assertRaises(HTTPException) as exc_nf:
            await CU36VestidorVirtualRaController.obtener_prenda_ar(_FakeConn(), emp_id, prenda_id)
        self.assertEqual(exc_nf.exception.status_code, 404)

        prenda_row = {
            "id": ar_id,
            "prenda_id": prenda_id,
            "codigo_prenda": "VES-01",
            "nombre_prenda": "Vestido Lino",
            "marca": "FashionStore",
            "categoria": "Vestidos",
            "modelo_url": "https://cdn.example.com/vestido.glb",
            "textura_url": "https://cdn.example.com/vestido.png",
            "puntos_ajuste": {"hombro": [0, 1.2, 0]},
            "talla_referencia": "M",
            "activo": True,
        }
        conn_ar = _FakeConn(
            fetch_handler=lambda sql, *args: [prenda_row] if "FROM prenda_ar" in sql else [],
            fetchrow_queue=[prenda_row, None],
        )
        lista = await CU36VestidorVirtualRaController.listar_prendas_ar(conn_ar, emp_id)
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0].prenda_id, prenda_id)

        sesion = await CU36VestidorVirtualRaController.iniciar_prueba(
            conn_ar,
            emp_id,
            usr_id,
            IniciarSesionArRequest(prenda_id=prenda_id),
        )
        self.assertEqual(sesion.estado, "iniciada")
        self.assertIsNotNone(sesion.avatar)
        self.assertIn("cintura", sesion.avatar.medidas)
        self.assertEqual(len([q for q in conn_ar.executed if "INSERT INTO medida_corporal" in q[0]]), 5)

        fin_ok = await CU36VestidorVirtualRaController.finalizar_prueba(
            _FakeConn(execute_result="UPDATE 1"),
            emp_id,
            sesion_id,
            FinalizarSesionArRequest(estado="completada"),
        )
        self.assertEqual(fin_ok["status"], "ok")

        with self.assertRaises(HTTPException) as exc_ses:
            await CU36VestidorVirtualRaController.finalizar_prueba(
                _FakeConn(execute_result="UPDATE 0"),
                emp_id,
                sesion_id,
                FinalizarSesionArRequest(estado="completada"),
            )
        self.assertEqual(exc_ses.exception.status_code, 404)

    async def test_cu36_decart_lucy_contrato_errores_y_fallback(self):
        """CU-36: Verifica 503 sin DECART_API_KEY, 502 si rechaza credenciales, 200 y fallback de prompt."""
        emp_id, usr_id, prenda_id = uuid4(), uuid4(), uuid4()

        with patch.dict(os.environ, {"DECART_API_KEY": ""}, clear=False), patch.object(
            vestidor_ar_service,
            "get_settings",
            return_value=SimpleNamespace(decart_api_key="", decart_model="lucy-vton-3.6", decart_api_url="https://api.decart.ai/v1"),
        ):
            with self.assertRaises(HTTPException) as exc_503:
                await vestidor_ar_service.obtener_sesion_decart_lucy(_FakeConn(), emp_id, usr_id)
            self.assertEqual(exc_503.exception.status_code, 503)

        mock_client = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_client

        mock_client.post.return_value = SimpleNamespace(status_code=401)
        with patch.dict(os.environ, {"DECART_API_KEY": "decart_key_test"}, clear=False), patch(
            "app.services.vestidor_ar_service.httpx.AsyncClient", return_value=mock_ctx
        ):
            with self.assertRaises(HTTPException) as exc_502:
                await vestidor_ar_service.obtener_sesion_decart_lucy(_FakeConn(), emp_id, usr_id)
            self.assertEqual(exc_502.exception.status_code, 502)

        mock_client.post.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"client_token": "tok_rt_999", "webrtc_url": "wss://rt.decart.ai/s/999"},
        )
        with patch.dict(os.environ, {"DECART_API_KEY": "decart_key_test"}, clear=False), patch(
            "app.services.vestidor_ar_service.httpx.AsyncClient", return_value=mock_ctx
        ):
            sess = await vestidor_ar_service.obtener_sesion_decart_lucy(_FakeConn(), emp_id, usr_id)
            self.assertEqual(sess["motor"], "decart-lucy-vton")
            self.assertEqual(sess["token"], "tok_rt_999")
            self.assertEqual(sess["stream_url"], "wss://rt.decart.ai/s/999")

        # Fallo de red con API key presente -> fallback a stream directo
        mock_client.post.side_effect = RuntimeError("Timeout Decart")
        with patch.dict(os.environ, {"DECART_API_KEY": "decart_key_test"}, clear=False), patch(
            "app.services.vestidor_ar_service.httpx.AsyncClient", return_value=mock_ctx
        ):
            sess_fb = await vestidor_ar_service.obtener_sesion_decart_lucy(_FakeConn(), emp_id, usr_id)
            self.assertEqual(sess_fb["token"], "decart_key_test")
            self.assertTrue(sess_fb["stream_url"].startswith("wss://"))

        # Prompt Lucy VTON: reemplaza placeholder cdn.fashionstore.test por ruta API de prenda
        conn_prompt = _FakeConn(
            fetchrow_queue=[
                {"nombre": "Camisa Seda", "descripcion": "Suave", "marca": "FS", "imagen_url": "https://cdn.fashionstore.test/x.jpg", "categoria": "Camisas"}
            ]
        )
        prompt_res = await vestidor_ar_service.preparar_prompt_lucy_vton(
            conn_prompt, emp_id, prenda_id, color_nombre="Azul", color_hex="#1E3A8A", talla="M"
        )
        self.assertEqual(prompt_res["image_url"], f"/api/v1/catalogo/prendas/{prenda_id}")
        self.assertIn("Camisa Seda", prompt_res["prompt"])
        self.assertIn("Azul", prompt_res["prompt"])

        with self.assertRaises(HTTPException) as exc_p404:
            await vestidor_ar_service.preparar_prompt_lucy_vton(_FakeConn(), emp_id, prenda_id)
        self.assertEqual(exc_p404.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
