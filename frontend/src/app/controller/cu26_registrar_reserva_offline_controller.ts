import { Injectable, signal } from '@angular/core';

/**
 * Controlador Web para CU-26: Registrar Reserva Offline (UUID Local en Outbox)
 */
@Injectable({ providedIn: 'root' })
export class CU26RegistrarReservaOfflineController {
  cargando = signal(false);
  error = signal<string | null>(null);
  reservaUuid = signal<string | null>(null);

  registrarReserva(payload: {
    sucursal_id: string;
    fecha_visita: string;
    probador: boolean;
    items: Array<{ variante_id: string; cantidad: number }>;
  }): string {
    this.cargando.set(true);
    this.error.set(null);

    try {
      const uuid = 'res-off-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7);
      const operacion = {
        id: uuid,
        tipo: 'reserva_offline',
        sucursal_id: payload.sucursal_id,
        payload: { ...payload, uuid, fecha_hora_local: new Date().toISOString() },
        creada_en: new Date().toISOString(),
        idempotency_key: 'RES-OFF-' + uuid,
        estado: 'pendiente'
      };

      const cola = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
      cola.push(operacion);
      localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));

      this.reservaUuid.set(uuid); //controlador1
      this.cargando.set(false);
      return uuid;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set('Fallo de almacenamiento local: ' + e.message);
      throw e;
    }
  }
}

