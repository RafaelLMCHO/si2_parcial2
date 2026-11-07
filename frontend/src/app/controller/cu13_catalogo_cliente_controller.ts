import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-13: Catálogo Cliente (Exploración, Búsqueda y Filtros)
 */
@Injectable({ providedIn: 'root' })
export class CU13CatalogoClienteController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  prendas = signal<any[]>([]);

  cargarCatalogo(params?: any): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/catalogo/prendas', { params }).pipe(
      tap({
        next: (res) => {
          this.prendas.set(Array.isArray(res) ? res : (res.items || []));
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

