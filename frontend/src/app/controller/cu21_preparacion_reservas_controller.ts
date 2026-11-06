import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-21: Preparación y Validación de Reservas en Tienda (Staff)
 */
@Injectable({ providedIn: 'root' })
export class CU21PreparacionReservasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  reservasSucursal = signal<any[]>([]);

  cargarReservas(sucursalId?: string): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/reservas', { params: sucursalId ? { sucursal_id: sucursalId } : {} }).pipe(
      tap({
        next: (res) => {
          this.reservasSucursal.set(res.items || []);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  preparar(id: string): Observable<any> {
    return this.http.post<any>(`/api/v1/reservas/${id}/preparar`, {}).pipe(
      tap(() => this.cargarReservas().subscribe())
    );
  }

  completar(id: string): Observable<any> {
    return this.http.post<any>(`/api/v1/reservas/${id}/completar`, {}).pipe(
      tap(() => this.cargarReservas().subscribe())
    );
  }

  reportarIncidencia(id: string, detalle: string): Observable<any> {
    return this.http.post<any>(`/api/v1/reservas/${id}/incidencia`, { detalle }).pipe(
      tap(() => this.cargarReservas().subscribe())
    );
  }
}

