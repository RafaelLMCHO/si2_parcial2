import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';

/**
 * Controlador Web para CU-31: Sincronizar Operaciones Pendientes (Idempotencia RNF05)
 */
@Injectable({ providedIn: 'root' })
export class CU31SincronizarOperacionesController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  confirmados = signal<number>(0);
  conflictos = signal<number>(0);

  sincronizarLote(): Observable<any> {
    this.cargando.set(true);
    this.error.set(null);
    this.confirmados.set(0);
    this.conflictos.set(0);

    const raw = localStorage.getItem('cola_operaciones_offline');
    const cola: any[] = raw ? JSON.parse(raw) : [];
    const pendientes = cola.filter((o) => o.estado === 'pendiente');

    if (pendientes.length === 0) {
      this.cargando.set(false);
      return new Observable((obs) => {
        obs.next({ procesados_total: 0, confirmados: [], conflictos: [] });
        obs.complete();
      });
    }

    // Marcar como enviadas
    pendientes.forEach((p) => (p.estado = 'enviada'));
    localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));

    const payload = {
      dispositivo_id: 'WEB-PWA-01',
      operaciones: pendientes.map((p) => ({
        id: p.id,
        tipo: p.tipo,
        sucursal_id: p.sucursal_id || '11111111-1111-1111-1111-111111111101',
        payload: p.payload,
        creada_en: p.creada_en,
        idempotency_key: p.idempotency_key || 'IDEMP-' + p.id
      }))
    };

    return this.http.post<any>('/api/v1/sync', payload).pipe(
      tap({
        next: (res) => {
          this.cargando.set(false);
          const confirmadosList: string[] = res.confirmados || [];
          const conflictosList: any[] = res.conflictos || [];

          cola.forEach((op) => {
            if (confirmadosList.includes(op.id)) {
              op.estado = 'confirmada';
            } else if (conflictosList.some((c) => c.id === op.id)) {
              op.estado = 'en_conflicto';
            }
          });

          localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));
          this.confirmados.set(confirmadosList.length);
          this.conflictos.set(conflictosList.length);
        }
      }),
      catchError((err) => {
        // RNF: Sección 5.4 - Prohibición absoluta de borrado y revertir a pendiente
        cola.forEach((op) => {
          if (op.estado === 'enviada') {
            op.estado = 'pendiente';
          }
        });
        localStorage.setItem('cola_operaciones_offline', JSON.stringify(cola));
        this.cargando.set(false);
        this.error.set('Corte de red en transmisión. Transacciones preservadas en cola: ' + err.message);
        return throwError(() => err);
      })
    );
  }
}

