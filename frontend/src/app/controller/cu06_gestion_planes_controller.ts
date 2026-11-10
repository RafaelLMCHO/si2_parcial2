import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-06: Gestión de Planes SaaS (Superadmin)
 */
@Injectable({ providedIn: 'root' })
export class CU06GestionPlanesController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  planes = signal<any[]>([]);

  cargarPlanes(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/saas/planes').pipe(
      tap({
        next: (res) => {
          this.planes.set(Array.isArray(res) ? res : (res.items || []));
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  crearPlan(plan: any): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/saas/planes', plan).pipe(
      tap({
        next: () => this.cargarPlanes().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  actualizarPlan(planId: string | number, plan: any): Observable<any> {
    this.cargando.set(true);
    return this.http.put<any>(`/api/v1/saas/planes/${planId}`, plan).pipe(
      tap({
        next: () => this.cargarPlanes().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  eliminarPlan(planId: string | number): Observable<any> {
    this.cargando.set(true);
    return this.http.delete<any>(`/api/v1/saas/planes/${planId}`).pipe(
      tap({
        next: () => this.cargarPlanes().subscribe(),
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }
}

