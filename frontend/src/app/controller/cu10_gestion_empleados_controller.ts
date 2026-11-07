import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-10: Gestión de Empleados, Usuarios y Roles
 */
@Injectable({ providedIn: 'root' })
export class CU10GestionEmpleadosController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  empleados = signal<any[]>([]);

  cargarEmpleados(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/empleados').pipe(
      tap({
        next: (res) => {
          this.empleados.set(Array.isArray(res) ? res : (res.items || []));
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  crearEmpleado(data: any): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/empleados', data).pipe(
      tap({
        next: () => this.cargarEmpleados().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

