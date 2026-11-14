import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, throwError, of } from 'rxjs';
import { OfflineQueueService } from '../core/offline-queue.service';
import { VentasOfflineStore } from '../core/ventas-offline-store.service';

/**
 * Controlador Web para CU-31: Sincronizar Operaciones Pendientes (Idempotencia RNF05)
 */
@Injectable({ providedIn: 'root' })
export class CU31SincronizarOperacionesController {
  private readonly http = inject(HttpClient);
  private readonly offlineQueue = inject(OfflineQueueService);
  private readonly ventasStore = inject(VentasOfflineStore);

  cargando = signal(false);
  error = signal<string | null>(null);
  confirmados = signal<number>(0);
  conflictos = signal<number>(0);

  sincronizarLote(): Observable<any> {
    if (this.cargando()) {
      return of({ procesados_total: 0, confirmados: [], conflictos: [] });
    }
    this.cargando.set(true);
    this.error.set(null);
    this.confirmados.set(0);
    this.conflictos.set(0);

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

    const localPendientes = cola.filter(
      (o) => o && o.tipo !== 'venta_offline' && (o.estado === 'pendiente' || o.estado === 'enviada'),
    );
    const ventasPendientes = this.ventasStore.listPendientes();
    const pendientes = [...localPendientes, ...ventasPendientes];

    if (pendientes.length === 0) {
      this.cargando.set(false);
      this.offlineQueue.refreshStatus();
      return new Observable((obs) => {
        obs.next({ procesados_total: 0, confirmados: [], conflictos: [] });
        obs.complete();
      });
    }

    // Marcar como enviadas
    localPendientes.forEach((p) => (p.estado = 'enviada'));
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));
    }
    this.ventasStore.markEnviadas(ventasPendientes.map((v) => v.id));

    const payload = {
      dispositivo_id: 'WEB-PWA-01',
      operaciones: pendientes.map((p) => ({
        id: p.id,
        tipo: p.tipo,
        sucursal_id: p.sucursal_id || p.payload?.sucursal_id || '11111111-1111-1111-1111-111111111101',
        payload: p.payload,
        creada_en: p.creada_en,
        idempotency_key: p.idempotency_key || 'IDEMP-' + p.id,
      })),
    };

    return this.http.post<any>('/api/v1/sync', payload).pipe(
      tap({
        next: (res) => {
          this.cargando.set(false);
          const confirmadosList: string[] = res.confirmados || [];
          const conflictosList: any[] = res.conflictos || [];

          cola.forEach((op) => {
            if (op && op.tipo !== 'venta_offline') {
              if (confirmadosList.includes(op.id)) {
                op.estado = 'confirmada';
                delete op.ultimo_error;
              } else {
                const conflicto = conflictosList.find((c: any) => c.id === op.id);
                if (conflicto) {
                  op.estado = 'en_conflicto';
                  op.ultimo_error = conflicto.detalle || conflicto.causa || 'Conflicto de stock al sincronizar';
                }
              }
            }
          });

          this.ventasStore.applySyncResult(confirmadosList, conflictosList);

          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));
          }
          this.offlineQueue.refreshStatus();
          this.confirmados.set(confirmadosList.length);
          this.conflictos.set(conflictosList.length);
        },
      }),
      catchError((err) => {
        // RNF: Sección 5.4 - Prohibición absoluta de borrado y revertir a pendiente
        cola.forEach((op) => {
          if (op && op.tipo !== 'venta_offline' && op.estado === 'enviada') {
            op.estado = 'pendiente';
          }
        });
        this.ventasStore.revertEnviadas();

        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));
        }
        this.offlineQueue.refreshStatus();
        this.cargando.set(false);
        this.error.set('Corte de red en transmisión. Transacciones preservadas en cola: ' + (err?.message || 'sin red'));
        return throwError(() => err);
      }),
    );
  }
}
