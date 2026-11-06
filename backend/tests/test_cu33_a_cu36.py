import io
import sys
import unittest
from unittest.mock import MagicMock

# Mock de dependencias opcionales de BD para pruebas unitarias sin conexión
if "asyncpg" not in sys.modules:
    sys.modules["asyncpg"] = MagicMock()

from uuid import uuid4

import numpy as np
import openpyxl

from app.controller.cu33_reportes_convencionales_controller import CU33ReportesConvencionalesController
from app.controller.cu34_reporte_generativo_ia_controller import CU34ReporteGenerativoIaController
from app.controller.cu35_dashboard_analitico_ml_controller import CU35DashboardAnaliticoMlController
from app.controller.cu36_vestidor_virtual_ra_controller import CU36VestidorVirtualRaController
from app.schemas.inteligencia import ExportarReporteRequest
from app.services.ia_reporte_service import (
    clasificar_intencion_whitelist,
    generar_excel,
    generar_pdf,
)
from app.services.ml_analytics_service import generar_audio_tts_sintesis


class TestCU33aCU36(unittest.TestCase):
    def test_cu33_controller_methods_exist(self):
        """Verifica que el controlador CU-33 exponga los métodos de reportes."""
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "obtener_dashboard"))
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "consultar_ventas_periodo"))
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "consultar_rotacion_stock"))
        self.assertTrue(hasattr(CU33ReportesConvencionalesController, "consultar_top_prendas"))

    def test_cu34_whitelist_clasificacion(self):
        """Verifica la regla BR-08 de whitelist segura para lenguaje natural."""
        # 1. Ventas por sucursal
        intent, params = clasificar_intencion_whitelist("Mostrame las ventas de septiembre agrupadas por sucursal")
        self.assertEqual(intent, "ventas_por_sucursal")
        self.assertEqual(params.get("mes"), 9)

        # 2. Top 10 prendas más vendidas
        intent2, params2 = clasificar_intencion_whitelist("¿Cuáles fueron los diez productos más vendidos este mes?")
        self.assertEqual(intent2, "top_productos_vendidos")
        self.assertEqual(params2.get("limite"), 10)

        # 3. Gráfico temporal de ventas
        intent3, _ = clasificar_intencion_whitelist("Generá un gráfico de ventas por semana")
        self.assertEqual(intent3, "ventas_temporales_semana")

        # 4. Stock crítico y rotación
        intent4, _ = clasificar_intencion_whitelist("Rotación y stock crítico por categoría")
        self.assertEqual(intent4, "rotacion_stock_critico")

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

        # Cargar libro con openpyxl para verificar estructura
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
        """Verifica la generación de audio WAV sintetizado para TTS."""
        texto = "Ventas proyectadas de 180 unidades para camisetas en noviembre."
        res = generar_audio_tts_sintesis(texto)
        self.assertIsNotNone(res.audio_base64)
        self.assertEqual(res.mime_type, "audio/wav")
        self.assertGreater(res.duracion_estimada_segundos, 1.0)

    def test_cu36_controller_methods_exist(self):
        """Verifica que el controlador CU-36 exponga los métodos de vestidor virtual."""
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "listar_prendas_ar"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "obtener_prenda_ar"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "obtener_avatar_usuario"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "iniciar_prueba"))
        self.assertTrue(hasattr(CU36VestidorVirtualRaController, "finalizar_prueba"))


if __name__ == "__main__":
    unittest.main()
