import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robustness_base import (
    setup_canvas, draw_actor, draw_boundary, draw_controller, draw_entity,
    draw_actor_link, draw_call_arrow, draw_crud_arrow, save_and_close
)

# -------------------------------------------------------------------------
# CU-29: Validar comprobante y procesar cambio mediante QR offline
# -------------------------------------------------------------------------
def generate_cu29(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-29: VALIDAR COMPROBANTE Y PROCESAR CAMBIO CON QR OFFLINE",
        "Actor: Cajero / Encargado | Boundary: QrScannerUI | Controller: process_qr_change() | Entidades: CambioPrenda, CambioPrendaDetalle, LocalVenta, LocalInventario"
    )
    draw_actor(ax, 0.10, 0.50, "Cajero / Encargado", "Personal de Tienda")
    draw_boundary(ax, 0.30, 0.50, "QrScannerUI", "qr-validator.component / Flutter")
    draw_controller(ax, 0.55, 0.50, "validarQrYCambio()", "cambio_service.dart")
    
    draw_entity(ax, 0.88, 0.80, "CambioPrenda", "db / cambio_prenda")
    draw_entity(ax, 0.88, 0.60, "CambioDetalle", "db / cambio_prenda_detalle")
    draw_entity(ax, 0.88, 0.40, "LocalVenta", "sqlite / venta (verificar QR)")
    draw_entity(ax, 0.88, 0.20, "LocalInventario", "sqlite / inventario (reingreso/salida)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "scanQrTicket()\n(firma_qr, prenda_in, prenda_out)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "crear registro cambio/devolución", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "POST", "detalle prendas devueltas/entregadas", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "validar autenticidad hash firma QR", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "PATCH", "ajustar stock (entrada/salida)", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu29_validar_comprobante_qr_offline")

# -------------------------------------------------------------------------
# CU-30: Consultar cola de operaciones pendientes offline (estados)
# -------------------------------------------------------------------------
def generate_cu30(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-30: CONSULTAR COLA DE OPERACIONES PENDIENTES OFFLINE",
        "Actor: Cliente / Personal | Boundary: SyncQueueUI | Controller: get_sync_queue() | Entidades: OperacionPendienteLocal, DispositivoOffline, EstadoSync"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente / Personal", "Usuario Local")
    draw_boundary(ax, 0.30, 0.50, "SyncQueueUI", "sync-queue.screen / PWA bar")
    draw_controller(ax, 0.55, 0.50, "listarColaLocal()", "sync_queue_manager.dart")
    
    draw_entity(ax, 0.88, 0.80, "ColaOffline", "sqlite / operacion_pendiente")
    draw_entity(ax, 0.88, 0.60, "Dispositivo", "sqlite / dispositivo_offline")
    draw_entity(ax, 0.88, 0.40, "LocalVenta", "sqlite / venta (pendientes)")
    draw_entity(ax, 0.88, 0.20, "LocalReserva", "sqlite / reserva (pendientes)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "verColaOperaciones()\n(filtro: pendiente/fallida)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "consultar transacciones en cola", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "verificar UUID del dispositivo", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "detalles de ventas offline asociadas", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "detalles de reservas offline", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu30_consultar_cola_operaciones_offline")

# -------------------------------------------------------------------------
# CU-31: Sincronizar operaciones pendientes (Idempotencia RNF05)
# -------------------------------------------------------------------------
def generate_cu31(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-31: SINCRONIZAR OPERACIONES PENDIENTES (IDEMPOTENCIA RNF05)",
        "Actor: Agente Sync / Cliente | Boundary: SyncManagerUI | Controller: process_sync_batch() | Entidades: OperacionPendiente, Venta, Inventario, DispositivoOffline, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Agente Sync", "Sync Engine / Cliente")
    draw_boundary(ax, 0.30, 0.50, "SyncStatusUI", "sync-status.component")
    draw_controller(ax, 0.55, 0.50, "sync_batch()", "sync_service.py")
    
    draw_entity(ax, 0.88, 0.82, "OperacionPendiente", "db / operacion_pendiente")
    draw_entity(ax, 0.88, 0.66, "Venta", "db / venta (idempotent UUID)")
    draw_entity(ax, 0.88, 0.50, "Inventario", "db / inventario (kardex sync)")
    draw_entity(ax, 0.88, 0.34, "Dispositivo", "db / dispositivo_offline")
    draw_entity(ax, 0.88, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/sync/batch\n(operaciones[], dispositivo_uuid)")
    
    draw_crud_arrow(ax, 0.63, 0.54, 0.81, 0.82, "GET/POST", "validar clave de idempotencia (RNF05)", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.52, 0.81, 0.66, "POST", "persistir venta definitiva", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "PATCH", "actualizar stock central y kardex", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.34, "PATCH", "actualizar ultima_sincronizacion", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.46, 0.81, 0.18, "POST", "auditar sincronización de lote", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu31_sincronizar_operaciones_idempotencia")

# -------------------------------------------------------------------------
# CU-32: Resolver conflictos de sincronizacion (FIFO y Manual)
# -------------------------------------------------------------------------
def generate_cu32(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-32: RESOLVER CONFLICTOS DE SINCRONIZACIÓN",
        "Actor: Encargado / Admin | Boundary: ConflictResolverUI | Controller: resolve_sync_conflict() | Entidades: ConflictoSync, OperacionPendiente, Inventario, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Encargado / Admin", "Resolutor")
    draw_boundary(ax, 0.30, 0.50, "ConflictResolverUI", "conflictos-sync.component")
    draw_controller(ax, 0.55, 0.50, "resolverConflicto()", "sync_service.py")
    
    draw_entity(ax, 0.88, 0.80, "ConflictoSync", "db / sync_conflicto")
    draw_entity(ax, 0.88, 0.60, "OperacionPendiente", "db / operacion_pendiente")
    draw_entity(ax, 0.88, 0.40, "Inventario", "db / inventario (ajuste forzado)")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/sync/conflictos/resolver\n(conflicto_id, accion: FIFO / RECHAZAR)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "PATCH", "marcar conflicto resuelto", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "PATCH", "cambiar estado de operacion", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "PATCH", "aplicar resolución sobre inventario", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar decisión manual/FIFO", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu32_resolver_conflictos_sincronizacion")

# -------------------------------------------------------------------------
# CU-33: Generar reportes y dashboards convencionales
# -------------------------------------------------------------------------
def generate_cu33(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-33: GENERAR REPORTES Y DASHBOARDS CONVENCIONALES",
        "Actor: Admin Empresa / Encargado | Boundary: ReportsDashboardUI | Controller: generate_standard_reports() | Entidades: Venta, Inventario, Prenda, Sucursal"
    )
    draw_actor(ax, 0.10, 0.50, "Admin / Encargado", "Gerencia Tenant")
    draw_boundary(ax, 0.30, 0.50, "ReportsDashboardUI", "reportes-graficos.component")
    draw_controller(ax, 0.55, 0.50, "getSalesKpis()", "reportes_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Venta", "db / venta (agregaciones)")
    draw_entity(ax, 0.88, 0.60, "Inventario", "db / inventario (rotación)")
    draw_entity(ax, 0.88, 0.40, "Prenda", "db / prenda (top ventas)")
    draw_entity(ax, 0.88, 0.20, "Sucursal", "db / sucursal (ventas por tienda)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/reportes/dashboard\n(fecha_desde, fecha_hasta, sucursal)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "calcular facturación y ticket promedio", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "rotación de stock por almacén", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "ranking top 10 prendas más vendidas", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "rendimiento comparativo de sucursales", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu33_generar_reportes_dashboards")

# -------------------------------------------------------------------------
# CU-34: Solicitar reporte generativo IA y exportar PDF/Excel (voz/texto)
# -------------------------------------------------------------------------
def generate_cu34(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-34: SOLICITAR REPORTE GENERATIVO IA Y EXPORTAR",
        "Actor: Admin Empresa / LLM Service | Boundary: GenerativeAiReportUI | Controller: generate_ai_report() | Entidades: ConsultaIa, ReporteExportado, Suscripcion, PostgreSQL Views"
    )
    draw_actor(ax, 0.10, 0.50, "Admin / LLM", "Usuario / Motor IA")
    draw_boundary(ax, 0.30, 0.50, "AiReportUI", "ia-reports.component (Mic / Text)")
    draw_controller(ax, 0.55, 0.50, "executeAiQuery()", "ia_generativa_service.py")
    
    draw_entity(ax, 0.88, 0.82, "ConsultaIa", "db / consulta_ia (prompts/tokens)")
    draw_entity(ax, 0.88, 0.66, "Suscripcion", "db / plan (verificar BR-03)")
    draw_entity(ax, 0.88, 0.50, "VistasTenant", "db / v_ventas, v_stock (whitelist)")
    draw_entity(ax, 0.88, 0.34, "ReporteExportado", "db / reporte_exportado (pdf/xlsx)")
    draw_entity(ax, 0.88, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/ia/reporte-generativo\n(prompt_lenguaje_natural, formato)")
    
    draw_crud_arrow(ax, 0.63, 0.54, 0.81, 0.82, "POST", "registrar consulta y tokens usados", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.52, 0.81, 0.66, "GET", "validar plan Profesional (BR-03)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "GET", "ejecutar SQL seguro contra vistas", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.34, "POST", "guardar archivo exportado descargable", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.46, 0.81, 0.18, "POST", "auditar ejecución de reporte IA", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu34_solicitar_reporte_generativo_ia")

# -------------------------------------------------------------------------
# CU-35: Consultar dashboard analitico ML con sintesis por audio (TTS)
# -------------------------------------------------------------------------
def generate_cu35(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-35: DASHBOARD ANALÍTICO ML CON SÍNTESIS AUDIO (TTS)",
        "Actor: Admin Empresa / Servicio ML | Boundary: MlAnalyticsUI | Controller: get_ml_analytics() | Entidades: ModeloMl, PrediccionDemanda, ClusterClientes, AudioSynthesizer"
    )
    draw_actor(ax, 0.10, 0.50, "Admin / ML Engine", "Gerencia / Scikit-Learn")
    draw_boundary(ax, 0.30, 0.50, "MlAnalyticsUI", "ml-dashboard.component (TTS Audio)")
    draw_controller(ax, 0.55, 0.50, "predictAndSynthesize()", "ml_analytics_service.py")
    
    draw_entity(ax, 0.88, 0.80, "ModeloMl", "db / modelo_ml (regresión/clustering)")
    draw_entity(ax, 0.88, 0.60, "PrediccionDemanda", "db / prediccion_demanda")
    draw_entity(ax, 0.88, 0.40, "ClusterClientes", "db / cluster_cliente (K-Means)")
    draw_entity(ax, 0.88, 0.20, "TtsAudioCache", "media / audio_tts_resumen.mp3")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/ml/analitica\n(empresa_id, solicitar_audio_tts)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "cargar artefacto de modelo scikit-learn", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "proyecciones de demanda próxima temp.", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "segmentación de clientes en clústeres", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST/GET", "sintetizar audio MP3 de KPIs hablados", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu35_consultar_dashboard_ml_audio_tts")

# -------------------------------------------------------------------------
# CU-36: Utilizar vestidor virtual con Realidad Aumentada (RA)
# -------------------------------------------------------------------------
def generate_cu36(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-36: VESTIDOR VIRTUAL CON REALIDAD AUMENTADA (RA)",
        "Actor: Cliente | Boundary: ArFittingRoomUI | Controller: render_ar_garment() | Entidades: PrendaRecursoAr, Variante, PoseDetectorML, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente", "Comprador Cámara/Web")
    draw_boundary(ax, 0.30, 0.50, "ArFittingRoomUI", "ar-fitting.screen (Camera Stream)")
    draw_controller(ax, 0.55, 0.50, "renderVirtualFitting()", "ar_fitting_service.dart")
    
    draw_entity(ax, 0.88, 0.80, "PrendaRecursoAr", "db / prenda_recurso_ar (modelo 3D)")
    draw_entity(ax, 0.88, 0.60, "Variante", "db / variante (talla, textura)")
    draw_entity(ax, 0.88, 0.40, "PoseDetectorML", "client / MediaPipe (landmarks)")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora (métrica RA)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "iniciarVestidorVirtual()\n(variante_id, camera_stream)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "descargar malla 3D / textura GLTF", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "verificar compatibilidad de dimensiones", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "superponer prenda en landmarks de cuerpo", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "registrar evento de interacción virtual", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu36_utilizar_vestidor_virtual_ra")

if __name__ == '__main__':
    out = os.path.join(os.getcwd(), 'Segundo-parcial', 'docs', 'diagramas')
    os.makedirs(out, exist_ok=True)
    generate_cu29(out)
    generate_cu30(out)
    generate_cu31(out)
    generate_cu32(out)
    generate_cu33(out)
    generate_cu34(out)
    generate_cu35(out)
    generate_cu36(out)
    print("Batch 3 (CU29-CU36) completed!")

