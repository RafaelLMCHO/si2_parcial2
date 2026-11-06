import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-14: Detalle de Producto, Variantes y Selección de Talla/Color
 */
@Injectable({ providedIn: 'root' })
export class CU14DetalleProductoController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  prenda = signal<any>(null);
  varianteSeleccionada = signal<any>(null);

  cargarDetalle(id: string): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>(`/api/v1/catalogo/prendas/${id}`).pipe(
      tap({
        next: (data) => {
          this.prenda.set(data);
          if (data.variantes && data.variantes.length > 0) {
            this.varianteSeleccionada.set(data.variantes[0]);
          }
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  seleccionarVariante(v: any) {
    this.varianteSeleccionada.set(v);
  }
}

