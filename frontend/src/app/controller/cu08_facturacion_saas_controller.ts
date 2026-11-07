import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-08: Facturación SaaS e Historial de Facturas
 */
@Injectable({ providedIn: 'root' })
export class CU08FacturacionSaasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  facturas = signal<any[]>([]);

  cargarFacturas(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/saas/facturas').pipe(
      tap({
        next: (res) => {
          this.facturas.set(Array.isArray(res) ? res : (res.items || []));
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

