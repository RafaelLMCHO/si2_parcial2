import { Injectable, inject, signal } from '@angular/core';
import { VentasOfflineStore, VentaOfflineRecord } from '../core/ventas-offline-store.service';
import { OfflineQueueService } from '../core/offline-queue.service';

/**
 * Controlador Web para CU-28: Registrar Venta de Contado Offline (Efectivo y Ticket Preliminar)
 */
@Injectable({ providedIn: 'root' })
export class CU28VentaContadoOfflineController {
  private readonly ventasStore = inject(VentasOfflineStore);
  private readonly offlineQueue = inject(OfflineQueueService);

  cargando = signal(false);
  error = signal<string | null>(null);
  ticketPreliminar = signal<any>(null);

  registrarVenta(datos: {
    sucursal_id: string;
    usuario_id: string;
    cliente_nombre: string;
    cliente_documento: string;
    lineas: Array<{ variante_id: string; sku: string; cantidad: number; precio_unitario: number }>;
    total: number;
    metodo_pago: string;
  }): any {
    // Restricción obligatoria Sección 7.2: solo efectivo
    if (datos.metodo_pago.toLowerCase() !== 'efectivo') {
      this.error.set('En contingencia offline solo se admiten cobros de contado en efectivo.');
      throw new Error(this.error()!);
    }

    this.cargando.set(true);
    this.error.set(null);

    try {
      const uuid = 'venta-off-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7);
      const payload = {
        uuid,
        sucursal_id: datos.sucursal_id,
        usuario_id: datos.usuario_id,
        cliente_nombre: datos.cliente_nombre || 'Consumidor Final',
        cliente_documento: datos.cliente_documento || '0',
        fecha_hora_local: new Date().toISOString(),
        lineas: datos.lineas,
        total: datos.total,
        forma_pago: 'efectivo',
        estado: 'pendiente',
        leyenda_ticket: 'VENTA EN MODO OFFLINE - PENDIENTE DE SINCRONIZACIÓN',
      };

      const operacion: VentaOfflineRecord = {
        id: uuid,
        tipo: 'venta_offline',
        sucursal_id: datos.sucursal_id,
        payload,
        creada_en: payload.fecha_hora_local,
        idempotency_key: 'VENTA-OFF-' + uuid,
        estado: 'pendiente',
        intentos: 0,
      };

      this.ventasStore.enqueue(operacion);
      this.offlineQueue.refreshStatus();

      this.ticketPreliminar.set(payload);
      this.cargando.set(false);
      return payload;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set('Error crítico al escribir en almacenamiento local: ' + e.message);
      throw e;
    }
  }
}
