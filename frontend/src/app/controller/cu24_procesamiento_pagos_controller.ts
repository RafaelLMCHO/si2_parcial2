import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-24: Procesamiento de Pagos, Pasarelas y Reembolsos
 */
@Injectable({ providedIn: 'root' })
export class CU24ProcesamientoPagosController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  pagoActual = signal<any>(null);

  crearIntencion(ventaId: string, pasarela: string = 'stripe'): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/pagos/intencion', { venta_id: ventaId, pasarela }).pipe(
      tap({
        next: (res) => {
          this.pagoActual.set(res);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  consultarEstado(pagoId: string): Observable<any> {
    return this.http.get<any>(`/api/v1/pagos/${pagoId}`).pipe(
      tap({
        next: (res) => this.pagoActual.set(res)
      })
    );
  }

  reembolsar(pagoId: string, motivo: string, monto?: number): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>(`/api/v1/pagos/${pagoId}/reembolsar`, { motivo, monto }).pipe(
      tap({
        next: () => this.cargando.set(false),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

