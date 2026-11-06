import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-19: Creación de Reservas y Probador
 */
@Injectable({ providedIn: 'root' })
export class CU19CreacionReservasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  reservaCreada = signal<any>(null);

  crearReserva(payload: {
    sucursal_id: string;
    fecha_visita: string;
    probador: boolean;
    items: Array<{ variante_id: string; cantidad: number }>;
  }): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/reservas', payload).pipe(
      tap({
        next: (res) => {
          this.reservaCreada.set(res);
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

