import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-15: Gestión de Proveedores
 */
@Injectable({ providedIn: 'root' })
export class CU15GestionProveedoresController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  proveedores = signal<any[]>([]);

  cargarProveedores(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/proveedores').pipe(
      tap({
        next: (res) => {
          this.proveedores.set(Array.isArray(res) ? res : (res.items || []));
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

