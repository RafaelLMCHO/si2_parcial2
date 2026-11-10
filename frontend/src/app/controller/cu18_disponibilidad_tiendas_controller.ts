import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-18: Disponibilidad en Tiendas / Búsqueda Omnicanal
 */
@Injectable({ providedIn: 'root' })
export class CU18DisponibilidadTiendasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  disponibilidad = signal<any[]>([]);

  consultarDisponibilidad(prendaId: string): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>(`/api/v1/inventario/prendas/${prendaId}/disponibilidad`).pipe(
      tap({
        next: (res) => {
          this.disponibilidad.set(res.sucursales || res.tiendas || []);
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

