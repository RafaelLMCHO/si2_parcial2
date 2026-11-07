import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-20: Consulta y Gestión de Reservas por Cliente
 */
@Injectable({ providedIn: 'root' })
export class CU20ConsultaReservasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  misReservas = signal<any[]>([]);

  cargarMisReservas(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/reservas/mis-reservas').pipe(
      tap({
        next: (res) => {
          this.misReservas.set(res.items || []);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  cancelarReserva(id: string, motivo?: string): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>(`/api/v1/reservas/${id}/cancelar`, { motivo }).pipe(
      tap({
        next: () => this.cargarMisReservas().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

