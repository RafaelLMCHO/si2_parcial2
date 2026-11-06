import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-11: Gestión de Sucursales
 */
@Injectable({ providedIn: 'root' })
export class CU11GestionSucursalesController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  sucursales = signal<any[]>([]);

  cargarSucursales(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/sucursales').pipe(
      tap({
        next: (res) => {
          this.sucursales.set(Array.isArray(res) ? res : (res.items || []));
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  crearSucursal(data: any): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/sucursales', data).pipe(
      tap({
        next: () => this.cargarSucursales().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

