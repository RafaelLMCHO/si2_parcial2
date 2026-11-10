import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-07: Suscripciones SaaS y Pagos Stripe
 */
@Injectable({ providedIn: 'root' })
export class CU07SuscripcionesSaasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  suscripcion = signal<any>(null);

  obtenerSuscripcion(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/mi-suscripcion').pipe(
      tap({
        next: (res) => {
          this.suscripcion.set(res);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  cambiarPlan(planCodigoOrId: string): Observable<any> {
    this.cargando.set(true);
    const body = /^\d+$/.test(planCodigoOrId.trim())
      ? { plan_id: Number(planCodigoOrId.trim()) }
      : { plan_codigo: planCodigoOrId.trim() };
    return this.http.put<any>('/api/v1/mi-suscripcion', body).pipe(
      tap({
        next: (res) => {
          this.suscripcion.set(res);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  cancelarSuscripcion(motivo: string = 'Cancelacion solicitada por el administrador'): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/mi-suscripcion/cancelar', { motivo }).pipe(
      tap({
        next: (res) => {
          this.suscripcion.set(res);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

