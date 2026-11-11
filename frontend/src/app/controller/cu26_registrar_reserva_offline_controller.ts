import { Injectable, inject, signal } from '@angular/core';
import { OfflineQueueService } from '../core/offline-queue.service';

export interface ReservaOfflineItemPayload {
  variante_id: string;
  cantidad: number;
  sku?: string;
  prenda_nombre?: string;
  talla?: string;
  color?: string;
}

export interface ReservaOfflinePayload {
  sucursal_id: string;
  sucursal_nombre?: string | null;
  fecha_visita: string;
  probador: boolean;
  items: ReservaOfflineItemPayload[];
}

export function generarUuidV4(): string {
  if (typeof crypto !== 'undefined') {
    if (typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    if (typeof crypto.getRandomValues === 'function') {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      bytes[6] = (bytes[6] & 0x0f) | 0x40;
      bytes[8] = (bytes[8] & 0x3f) | 0x80;
      const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0'));
      return `${hex.slice(0, 4).join('')}-${hex.slice(4, 6).join('')}-${hex.slice(6, 8).join('')}-${hex.slice(8, 10).join('')}-${hex.slice(10, 16).join('')}`;
    }
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Controlador Web para CU-26: Registrar Reserva Offline (UUID Local en Outbox)
 */
@Injectable({ providedIn: 'root' })
export class CU26RegistrarReservaOfflineController {
  private readonly offlineQueue = inject(OfflineQueueService);

  cargando = signal(false);
  error = signal<string | null>(null);
  reservaUuid = signal<string | null>(null);
  codigoLocal = signal<string | null>(null);

  registrarReserva(payload: ReservaOfflinePayload): string {
    this.cargando.set(true);
    this.error.set(null);

    try {
      const sucursalId = (payload.sucursal_id || '').trim();
      if (!sucursalId) {
        throw new Error('Debe seleccionar una sucursal válida.');
      }
      if (!payload.items || payload.items.length === 0) {
        throw new Error('Debe incluir al menos una prenda para reservar.');
      }

      const uuid = generarUuidV4();
      const codigoLocal = `RES-OFF-${uuid.slice(0, 8).toUpperCase()}`;
      const nowIso = new Date().toISOString();

      const operacion = {
        id: uuid,
        tipo: 'reserva_offline',
        sucursal_id: sucursalId,
        sucursal_nombre: payload.sucursal_nombre || null,
        codigo_local: codigoLocal,
        payload: {
          ...payload,
          sucursal_id: sucursalId,
          uuid,
          codigo_local: codigoLocal,
          fecha_hora_local: nowIso,
        },
        creada_en: nowIso,
        idempotency_key: 'IDEMP-' + uuid,
        estado: 'pendiente',
      };

      const colaRaw = localStorage.getItem('cola_operaciones_offline');
      const cola: any[] = colaRaw ? JSON.parse(colaRaw) : [];
      cola.push(operacion);
      localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));
      this.offlineQueue.refreshStatus();

      this.reservaUuid.set(uuid);
      this.codigoLocal.set(codigoLocal);
      this.cargando.set(false);
      return uuid;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set(e?.message || 'Fallo de almacenamiento local');
      throw e;
    }
  }

  listarPendientes(): any[] {
    if (typeof localStorage === 'undefined') {
      return [];
    }
    try {
      const cola: any[] = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
      return (Array.isArray(cola) ? cola : []).filter(
        (op) => op && op.tipo === 'reserva_offline' && op.estado !== 'confirmada',
      );
    } catch {
      return [];
    }
  }

  esReservaLocal(id: string): boolean {
    if (typeof localStorage === 'undefined') {
      return false;
    }
    try {
      const cola: any[] = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
      return (Array.isArray(cola) ? cola : []).some(
        (op) => op && op.id === id && op.tipo === 'reserva_offline' && op.estado !== 'confirmada',
      );
    } catch {
      return false;
    }
  }

  cancelarReservaLocal(id: string): boolean {
    if (typeof localStorage === 'undefined') {
      return false;
    }
    try {
      const cola: any[] = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
      if (!Array.isArray(cola)) {
        return false;
      }
      const next = cola.filter((op) => !(op && op.id === id && op.tipo === 'reserva_offline' && op.estado !== 'confirmada'));
      const changed = next.length !== cola.length;
      if (changed) {
        localStorage.setItem('cola_operaciones_offline', JSON.stringify(next));
        this.offlineQueue.refreshStatus();
      }
      return changed;
    } catch {
      return false;
    }
  }
}

