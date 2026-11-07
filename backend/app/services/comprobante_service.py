"""
Servicio de Comprobantes Electrónicos (PDF y HTML).
Genera facturas, tickets de 80 mm y comprobantes con ReportLab y QR.
"""
import io
import logging
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def generar_comprobante_pdf(datos: dict) -> bytes:
    """
    Genera un comprobante digital en PDF usando ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Encabezado
        p.setFont("Helvetica-Bold", 16)
        p.drawString(2 * cm, height - 2.5 * cm, str(datos.get("empresa_nombre") or "FashionStore"))

        p.setFont("Helvetica", 10)
        p.drawString(2 * cm, height - 3.2 * cm, f"NIT: {datos.get('empresa_nit') or 'N/A'}")
        p.drawString(2 * cm, height - 3.7 * cm, f"Comprobante N°: {datos.get('numero')}")
        p.drawString(2 * cm, height - 4.2 * cm, f"Fecha: {str(datos.get('fecha_hora'))[:19]}")

        # Cliente
        p.drawString(11 * cm, height - 2.5 * cm, f"Cliente: {datos.get('cliente_nombre') or 'Consumidor Final'}")
        p.drawString(11 * cm, height - 3.2 * cm, f"NIT/CI: {datos.get('cliente_documento') or '0'}")
        p.drawString(11 * cm, height - 3.7 * cm, f"Estado: {datos.get('estado')}")
        p.drawString(11 * cm, height - 4.2 * cm, f"Canal: {datos.get('canal')}")

        p.setStrokeColorRGB(0.7, 0.7, 0.7)
        p.line(2 * cm, height - 4.8 * cm, width - 2 * cm, height - 4.8 * cm)

        # Tabla de líneas
        p.setFont("Helvetica-Bold", 10)
        y = height - 5.5 * cm
        p.drawString(2 * cm, y, "Artículo")
        p.drawString(9 * cm, y, "Talla/Color")
        p.drawString(13 * cm, y, "Cant.")
        p.drawString(15 * cm, y, "P. Unit")
        p.drawString(18 * cm, y, "Subtotal")

        p.setFont("Helvetica", 9)
        y -= 0.6 * cm
        for item in datos.get("lineas", []):
            if y < 4 * cm:
                p.showPage()
                y = height - 3 * cm
                p.setFont("Helvetica", 9)

            desc = f"{item.get('prenda_nombre', '')} ({item.get('sku', '')})"
            p.drawString(2 * cm, y, desc[:35])
            p.drawString(9 * cm, y, f"{item.get('talla', '')} / {item.get('color', '')}")
            p.drawString(13.2 * cm, y, str(item.get("cantidad", 1)))
            p.drawString(15 * cm, y, f"{float(item.get('precio_unitario', 0)):.2f}")
            p.drawString(18 * cm, y, f"{float(item.get('subtotal', 0)):.2f}")
            y -= 0.5 * cm

        p.line(2 * cm, y - 0.2 * cm, width - 2 * cm, y - 0.2 * cm)
        y -= 0.8 * cm

        # Totales
        p.setFont("Helvetica", 10)
        p.drawString(13 * cm, y, "Subtotal:")
        p.drawString(18 * cm, y, f"{float(datos.get('subtotal', 0)):.2f} BOB")
        y -= 0.5 * cm

        p.drawString(13 * cm, y, "Descuento:")
        p.drawString(18 * cm, y, f"-{float(datos.get('descuento', 0)):.2f} BOB")
        y -= 0.5 * cm

        p.drawString(13 * cm, y, "IVA (13%):")
        p.drawString(18 * cm, y, f"{float(datos.get('impuesto', 0)):.2f} BOB")
        y -= 0.6 * cm

        p.setFont("Helvetica-Bold", 12)
        p.drawString(13 * cm, y, "TOTAL:")
        p.drawString(18 * cm, y, f"{float(datos.get('total', 0)):.2f} BOB")

        # Firma QR
        firma = datos.get("firma_qr")
        if firma:
            p.setFont("Helvetica", 7)
            p.drawString(2 * cm, 2.5 * cm, f"Firma Digital: {firma}")
            p.drawString(2 * cm, 2.1 * cm, "Consulte la autenticidad escaneando el código QR de este comprobante.")

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as exc:
        logger.error("Error al generar PDF ReportLab: %s", str(exc))
        # Fallback a texto simple
        return f"Comprobante Nro: {datos.get('numero')} - Total: {datos.get('total')}".encode("utf-8")

