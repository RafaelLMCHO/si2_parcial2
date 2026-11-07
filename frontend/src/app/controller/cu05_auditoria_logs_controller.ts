import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-05: Auditoría y Trazabilidad de Logs del Sistema
 */
@Injectable({ providedIn: 'root' })
export class CU05AuditoriaLogsController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  logs = signal<any[]>([]);

  cargarLogs(params?: any): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/auditoria/logs', { params }).pipe(
      tap({
        next: (res) => {
          this.logs.set(Array.isArray(res) ? res : (res.items || []));
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

