import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robustness_base import (
    setup_canvas, draw_actor, draw_boundary, draw_controller, draw_entity,
    draw_actor_link, draw_call_arrow, draw_crud_arrow, save_and_close
)

# -------------------------------------------------------------------------
# CU-21: Preparar reservas en sucursal (apartado fisico en probadores)
# -------------------------------------------------------------------------
def generate_cu21(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-21: PREPARAR RESERVAS EN SUCURSAL",
        "Actor: Encargado Sucursal | Boundary: PrepararReservaUI | Controller: preparar_reserva() | Entidades: Reserva, ReservaDetalle, Inventario, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Encargado", "Personal de Tienda")
    draw_boundary(ax, 0.30, 0.50, "PrepararReservaUI", "reservas-tienda.component")
    draw_controller(ax, 0.55, 0.50, "preparar_items()", "reserva_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Reserva", "db / reserva (preparada)")
    draw_entity(ax, 0.88, 0.60, "ReservaDetalle", "db / reserva_detalle (items)")
    draw_entity(ax, 0.88, 0.40, "Inventario", "db / inventario (apartado probador)")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "PATCH /api/v1/reservas/{id}/preparar\n(probador_asignado, checklist)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "PATCH", "marcar estado 'preparada'", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "verificar prendas por apartar", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "PATCH", "confirmar apartado físico", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar preparación reserva", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu21_preparar_reservas_sucursal")

# -------------------------------------------------------------------------
# CU-22: Realizar compra digital (checkout carrito)
# -------------------------------------------------------------------------
def generate_cu22(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-22: REALIZAR COMPRA DIGITAL (CHECKOUT E-COMMERCE)",
        "Actor: Cliente | Boundary: CheckoutUI | Controller: process_checkout() | Entidades: Carrito, Venta, VentaDetalle, Inventario, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente", "Comprador Online")
    draw_boundary(ax, 0.30, 0.50, "CheckoutUI", "checkout.component / Flutter")
    draw_controller(ax, 0.55, 0.50, "checkout()", "venta_service.py")
    
    draw_entity(ax, 0.88, 0.82, "Carrito", "db / carrito, carrito_detalle")
    draw_entity(ax, 0.88, 0.66, "Venta", "db / venta (canal=online)")
    draw_entity(ax, 0.88, 0.50, "VentaDetalle", "db / venta_detalle")
    draw_entity(ax, 0.88, 0.34, "Inventario", "db / inventario (descontar stock)")
    draw_entity(ax, 0.88, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/ventas/checkout\n(direccion_envio, metodo_pago)")
    
    draw_crud_arrow(ax, 0.63, 0.54, 0.81, 0.82, "GET/DELETE", "leer carrito / vaciar items", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.52, 0.81, 0.66, "POST", "crear orden de venta online", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "POST", "insertar líneas con precio unit.", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.34, "PATCH", "descontar stock de sucursal/almacén", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.46, 0.81, 0.18, "POST", "auditar compra digital", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu22_realizar_compra_digital")

# -------------------------------------------------------------------------
# CU-23: Realizar compra presencial en caja (POS online)
# -------------------------------------------------------------------------
def generate_cu23(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-23: REALIZAR COMPRA PRESENCIAL EN CAJA (POS ONLINE)",
        "Actor: Cajero | Boundary: PosTerminalUI | Controller: process_pos_sale() | Entidades: Venta, VentaDetalle, Inventario, MovimientoInventario, Pago"
    )
    draw_actor(ax, 0.10, 0.50, "Cajero", "Operador de Caja")
    draw_boundary(ax, 0.30, 0.50, "PosTerminalUI", "pos.component / Flutter")
    draw_controller(ax, 0.55, 0.50, "registrarVentaPOS()", "pos_service.py")
    
    draw_entity(ax, 0.88, 0.82, "Venta", "db / venta (canal=pos_fisico)")
    draw_entity(ax, 0.88, 0.66, "VentaDetalle", "db / venta_detalle")
    draw_entity(ax, 0.88, 0.50, "Inventario", "db / inventario (stock)")
    draw_entity(ax, 0.88, 0.34, "MovimientoInv", "db / movimiento_inventario")
    draw_entity(ax, 0.88, 0.18, "Pago", "db / pago (efectivo/qr)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/ventas/pos\n(items, cliente_ci, tipo_pago)")
    
    draw_crud_arrow(ax, 0.63, 0.54, 0.81, 0.82, "POST", "crear venta completada", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.52, 0.81, 0.66, "POST", "insertar líneas de prendas", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "PATCH", "descontar existencias sucursal", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.34, "POST", "kardex salida por venta", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.46, 0.81, 0.18, "POST", "registrar comprobante de pago", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu23_realizar_compra_presencial_caja")

# -------------------------------------------------------------------------
# CU-24: Gestionar pagos (integracion Stripe Sandbox)
# -------------------------------------------------------------------------
def generate_cu24(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-24: GESTIONAR PAGOS DIGITALES (STRIPE SANDBOX)",
        "Actor: Cliente / Pasarela | Boundary: PaymentStripeUI | Controller: process_stripe_payment() | Entidades: Pago, Venta, BitacoraAuditoria, StripeWebhook"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente / Stripe", "Pagador / Pasarela")
    draw_boundary(ax, 0.30, 0.50, "PaymentStripeUI", "stripe-elements.component")
    draw_controller(ax, 0.55, 0.50, "handlePayment()", "pago_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Pago", "db / pago (transaccion_id)")
    draw_entity(ax, 0.88, 0.60, "Venta", "db / venta (estado_pago)")
    draw_entity(ax, 0.88, 0.40, "StripeEvent", "gateway / PaymentIntent")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/pagos/stripe/intent\n(venta_id, payment_method_id)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "registrar intento de cobro", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "PATCH", "actualizar estado a pagado", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "POST", "confirmar webhook con Stripe API", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar conciliación de pago", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu24_gestionar_pagos_stripe")

# -------------------------------------------------------------------------
# CU-25: Descargar catalogo offline (IndexedDB / SQLite)
# -------------------------------------------------------------------------
def generate_cu25(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-25: DESCARGAR CATÁLOGO OFFLINE (CACHE LOCAL)",
        "Actor: Cliente / Cajero | Boundary: OfflineSyncUI | Controller: sync_catalog_offline() | Entidades: Prenda, Variante, PrecioHistorial, SQLiteCatalogCache"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente / Cajero", "Usuario Móvil / PWA")
    draw_boundary(ax, 0.30, 0.50, "OfflineSyncUI", "sync-status.component / Flutter")
    draw_controller(ax, 0.55, 0.50, "downloadCatalog()", "offline_sync_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Prenda", "db / prenda (backend)")
    draw_entity(ax, 0.88, 0.60, "Variante", "db / variante (backend)")
    draw_entity(ax, 0.88, 0.40, "PrecioHistorial", "db / precio_historial")
    draw_entity(ax, 0.88, 0.20, "LocalCatalogDB", "client / SQLite / IndexedDB")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/offline/catalogo\n(sucursal_id, last_sync_timestamp)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "consultar delta de prendas", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "obtener variantes y stock local", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "descargar lista de precios", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "PUT/POST", "reemplazar tabla local SQLite", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu25_descargar_catalogo_offline")

# -------------------------------------------------------------------------
# CU-26: Registrar reserva offline (UUID local)
# -------------------------------------------------------------------------
def generate_cu26(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-26: REGISTRAR RESERVA OFFLINE (UUID LOCAL)",
        "Actor: Cliente | Boundary: ReservaOfflineUI | Controller: save_offline_reservation() | Entidades: LocalReserva, LocalReservaDetalle, OperacionPendiente, LocalCatalogDB"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente", "App Móvil Offline")
    draw_boundary(ax, 0.30, 0.50, "ReservaOfflineUI", "reserva-form.screen (Flutter)")
    draw_controller(ax, 0.55, 0.50, "guardarReservaLocal()", "offline_reserva_repo.dart")
    
    draw_entity(ax, 0.88, 0.80, "LocalReserva", "sqlite / reserva (UUIDv4)")
    draw_entity(ax, 0.88, 0.60, "LocalResDetalle", "sqlite / reserva_detalle")
    draw_entity(ax, 0.88, 0.40, "ColaOffline", "sqlite / operacion_pendiente")
    draw_entity(ax, 0.88, 0.20, "LocalCatalogDB", "sqlite / stock_cache")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "submitReservaOffline()\n(generar client_uuid)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "insertar reserva local UUID", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "POST", "insertar prendas a reservar", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "POST", "encolar operación 'crear_reserva'", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "PATCH", "descontar stock de SQLite local", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu26_registrar_reserva_offline")

# -------------------------------------------------------------------------
# CU-27: Bloquear stock local offline con TTL (Soft-Lock)
# -------------------------------------------------------------------------
def generate_cu27(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-27: BLOQUEAR STOCK LOCAL OFFLINE CON TTL (SOFT-LOCK)",
        "Actor: Cajero / Sistema Local | Boundary: SoftLockUI | Controller: manage_soft_lock() | Entidades: LocalStockLock, LocalInventario, TimerTTL, OperacionPendiente"
    )
    draw_actor(ax, 0.10, 0.50, "Cajero / Sistema", "Agente Offline Local")
    draw_boundary(ax, 0.30, 0.50, "SoftLockUI", "pos-checkout-bar.component")
    draw_controller(ax, 0.55, 0.50, "applySoftLock()", "soft_lock_manager.dart")
    
    draw_entity(ax, 0.88, 0.80, "LocalStockLock", "sqlite / soft_lock (variante_id)")
    draw_entity(ax, 0.88, 0.60, "LocalInventario", "sqlite / inventario_local")
    draw_entity(ax, 0.88, 0.40, "TimerTTL", "memory / ttl_timer (15 min)")
    draw_entity(ax, 0.88, 0.20, "ColaOffline", "sqlite / operacion_pendiente")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "lockItemOffline()\n(variante_id, cantidad, ttl=900s)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "crear registro soft_lock con TTL", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "PATCH", "congelar unidades disponibles", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "POST", "programar expiración automática", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "evitar colisión local concurrente", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu27_bloquear_stock_offline_ttl")

# -------------------------------------------------------------------------
# CU-28: Registrar venta de contado offline (efectivo y ticket preliminar)
# -------------------------------------------------------------------------
def generate_cu28(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-28: REGISTRAR VENTA DE CONTADO OFFLINE",
        "Actor: Cajero | Boundary: PosOfflineUI | Controller: save_offline_sale() | Entidades: LocalVenta, LocalVentaDetalle, TicketFirmaQR, OperacionPendiente"
    )
    draw_actor(ax, 0.10, 0.50, "Cajero", "Terminal POS Offline")
    draw_boundary(ax, 0.30, 0.50, "PosOfflineUI", "pos-offline.screen")
    draw_controller(ax, 0.55, 0.50, "procesarVentaOffline()", "pos_offline_controller.dart")
    
    draw_entity(ax, 0.88, 0.80, "LocalVenta", "sqlite / venta (offline_cash)")
    draw_entity(ax, 0.88, 0.60, "LocalVentaDetalle", "sqlite / venta_detalle")
    draw_entity(ax, 0.88, 0.40, "TicketFirmaQR", "crypto / sha256_qr_ticket")
    draw_entity(ax, 0.88, 0.20, "ColaOffline", "sqlite / operacion_pendiente")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "confirmarCobroEfectivo()\n(cliente, items, monto_recibido)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "insertar venta offline con UUID", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "POST", "insertar líneas con precio congelado", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "POST", "generar firma digital QR preliminar", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "encolar en operacion_pendiente", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu28_registrar_venta_contado_offline")

if __name__ == '__main__':
    out = os.path.join(os.getcwd(), 'Segundo-parcial', 'docs', 'diagramas')
    os.makedirs(out, exist_ok=True)
    generate_cu21(out)
    generate_cu22(out)
    generate_cu23(out)
    generate_cu24(out)
    generate_cu25(out)
    generate_cu26(out)
    generate_cu27(out)
    generate_cu28(out)
    print("Batch 2 (CU21-CU28) completed!")

