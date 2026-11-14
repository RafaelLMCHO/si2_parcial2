import { Injectable, inject, signal } from '@angular/core';
import { VentasOfflineStore } from '../core/ventas-offline-store.service';

/**
 * Controlador Web para CU-30: Consultar Cola de Operaciones Pendientes Offline
 */
@Injectable({ providedIn: 'root' })
export class CU30ColaOperacionesOfflineController {
  private readonly ventasStore = inject(VentasOfflineStore);

  cargando = signal(false);
  operaciones = signal<any[]>([]);

  cargarCola(): any[] {
    this.cargando.set(true);
    let cola: any[] = [];
    if (typeof localStorage !== 'undefined') {
      try {
        const raw = localStorage.getItem('cola_operaciones_offline');
        cola = raw ? JSON.parse(raw) : [];
        if (!Array.isArray(cola)) cola = [];
      } catch {
        cola = [];
      }
    }

    const locales = cola.filter((o) => o && o.tipo !== 'venta_offline');
    const ventas = this.ventasStore.list();

    const map = new Map<string, any>();
    for (const item of [...locales, ...ventas]) {
      if (item && item.id) {
        map.set(item.id, item);
      }
    }
    const ops = Array.from(map.values());

    this.operaciones.set(ops);
    this.cargando.set(false);
    return ops;
  }
}
