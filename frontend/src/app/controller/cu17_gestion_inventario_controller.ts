import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-17: Gestión de Inventario, Kardex, Ajustes y Alertas
 */
@Injectable({ providedIn: 'root' })
export class CU17GestionInventarioController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  inventario = signal<any[]>([]);

  cargarInventario(params?: any): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/inventario', { params }).pipe(
      tap({
        next: (res) => {
          this.inventario.set(Array.isArray(res) ? res : (res.items || []));
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  registrarAjuste(ajuste: {
    sucursal_id: string;
    variante_id: string;
    cantidad: number;
    motivo: string;
  }): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/inventario/movimientos/ajuste', ajuste).pipe(
      tap({
        next: () => this.cargarInventario().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

