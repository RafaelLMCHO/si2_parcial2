import { Injectable, signal } from '@angular/core';

/**
 * Controlador Web para CU-29: Validar Comprobante y Procesar Cambio mediante QR Offline
 */
@Injectable({ providedIn: 'root' })
export class CU29ValidarQrCambioOfflineController {
  cargando = signal(false);
  error = signal<string | null>(null);
  ticketValidado = signal<any>(null);
  notaCambio = signal<any>(null);

  validarQr(qrData: string): boolean {
    this.cargando.set(true);
    this.error.set(null);

    try {
      const data = JSON.parse(qrData);
      if (data.fecha_hora_local) {
        const fecha = new Date(data.fecha_hora_local);
        const diffDias = Math.floor((Date.now() - fecha.getTime()) / (1000 * 3600 * 24));
        if (diffDias > 30) {
          this.cargando.set(false);
          this.error.set(`Plazo de cambio vencido (${diffDias} días transcurridos. Máximo 30 días según Regla BR-10).`);
          return false;
        }
      }
      this.ticketValidado.set(data);
      this.cargando.set(false);
      return true;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set('Código QR inválido o firma alterada: ' + e.message);
      return false;
    }
  }

  procesarCambio(datos: {
    sucursal_id: string;
    variante_devuelta_id: string;
    variante_nueva_id: string;
    motivo: string;
  }): any {
    this.cargando.set(true);
    try {
      const uuid = 'cambio-off-' + Date.now();
      const payload = {
        uuid,
        sucursal_id: datos.sucursal_id,
        venta_origen_uuid: this.ticketValidado()?.uuid,
        variante_devuelta_id: datos.variante_devuelta_id,
        variante_nueva_id: datos.variante_nueva_id,
        motivo: datos.motivo,
        fecha_hora_local: new Date().toISOString(),
        tipo_documento: 'NOTA DE CAMBIO PRELIMINAR - PENDIENTE DE SINCRONIZACIÓN'
      };

      const operacion = {
        id: uuid,
        tipo: 'cambio_offline',
        sucursal_id: datos.sucursal_id,
        payload,
        creada_en: payload.fecha_hora_local,
        idempotency_key: 'CAMBIO-OFF-' + uuid,
        estado: 'pendiente'
      };

      const cola = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
      cola.push(operacion);
      localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));

      this.notaCambio.set(payload);
      this.cargando.set(false);
      return payload;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set('Error guardando nota de cambio: ' + e.message);
      throw e;
    }
  }
}

