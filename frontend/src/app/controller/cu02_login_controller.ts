import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-02: Inicio de Sesión Multi-inquilino (Login)
 */
@Injectable({ providedIn: 'root' })
export class CU02LoginController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);

  login(credenciales: { email: string; password: string; empresa_slug?: string }): Observable<any> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http.post<any>('/api/v1/auth/login', credenciales).pipe(
      tap({
        next: (res) => {
          this.cargando.set(false);
          if (res.access_token) {
            localStorage.setItem('access_token', res.access_token);
          }
        },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err.error?.detail || 'Credenciales inválidas');
        }
      })
    );
  }
}

