import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-16: Gestión de Temporadas y Colecciones
 */
@Injectable({ providedIn: 'root' })
export class CU16GestionTemporadasController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  temporadas = signal<any[]>([]);

  cargarTemporadas(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/temporadas').pipe(
      tap({
        next: (res) => {
          this.temporadas.set(Array.isArray(res) ? res : (res.items || []));
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

