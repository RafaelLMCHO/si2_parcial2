import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-09: Métricas SaaS / Superadmin Dashboard
 */
@Injectable({ providedIn: 'root' })
export class CU09MetricasSaasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  metricas = signal<any>({});

  cargarMetricas(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/saas/metricas').pipe(
      tap({
        next: (data) => {
          this.metricas.set(data || {});
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

