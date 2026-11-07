import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-12: Catálogo Admin (Prendas, Categorías y Variantes)
 */
@Injectable({ providedIn: 'root' })
export class CU12CatalogoAdminController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  prendas = signal<any[]>([]);

  cargarPrendas(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/catalogo/admin/prendas').pipe(
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

  crearPrenda(prenda: any): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/catalogo/admin/prendas', prenda).pipe(
      tap({
        next: () => this.cargarPrendas().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

