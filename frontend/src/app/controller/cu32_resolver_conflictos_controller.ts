import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-32: Resolver Conflictos de Sincronización (FIFO y Manual)
 */
@Injectable({ providedIn: 'root' })
export class CU32ResolverConflictosController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  conflictos = signal<any[]>([]);

  cargarConflictos(sucursalId?: string): Observable<any> {
    this.cargando.set(true);
    const params: any = {};
    if (sucursalId) params.sucursal_id = sucursalId;

    return this.http.get<any[]>('/api/v1/sync/conflictos', { params }).pipe(
      tap({
        next: (data) => {
          this.conflictos.set(data || []);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  resolverConflicto(payload: {
    operacion_id: string;
    decision: 'ajustar' | 'aceptar' | 'rechazar' | 'sustituir';
    motivo?: string;
    detalle?: any;
  }): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/sync/conflictos/resolver', payload).pipe(
      tap({
        next: () => this.cargarConflictos().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

