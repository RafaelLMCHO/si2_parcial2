import { Injectable, signal } from '@angular/core';

/**
 * Controlador Web para CU-30: Consultar Cola de Operaciones Pendientes Offline
 */
@Injectable({ providedIn: 'root' })
export class CU30ColaOperacionesOfflineController {
  cargando = signal(false);
  operaciones = signal<any[]>([]);

  cargarCola(): any[] {
    this.cargando.set(true);
    const raw = localStorage.getItem('cola_operaciones_offline');
    const ops = raw ? JSON.parse(raw) : [];
    this.operaciones.set(ops);
    this.cargando.set(false);
    return ops;
  }
}

