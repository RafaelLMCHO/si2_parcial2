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
    return this.http.get<any>('/api/v1/saas/suscripcion/actual').pipe(
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

  cambiarPlan(planId: string): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/saas/suscripcion/cambiar', { plan_id: planId }).pipe(
      tap({
        next: () => this.obtenerSuscripcion().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

