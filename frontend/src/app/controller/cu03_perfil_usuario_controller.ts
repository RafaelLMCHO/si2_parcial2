import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-03: Perfil de Usuario y Cambio de Contraseña
 */
@Injectable({ providedIn: 'root' })
export class CU03PerfilUsuarioController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  perfil = signal<any>(null);

  cargarPerfil(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/users/me').pipe(
      tap({
        next: (data) => {
          this.perfil.set(data);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  cambiarPassword(passwords: {
    actual?: string;
    nueva?: string;
    password_actual?: string;
    password_nueva?: string;
  }): Observable<any> {
    this.cargando.set(true);
    const body = {
      password_actual: passwords.password_actual ?? passwords.actual ?? '',
      password_nueva: passwords.password_nueva ?? passwords.nueva ?? '',
    };
    return this.http.post<any>('/api/v1/users/me/password', body).pipe(
      tap({
        next: () => this.cargando.set(false),
        error: (err) => {
          this.error.set(err.error?.detail || 'Error al cambiar contraseña');
          this.cargando.set(false);
        }
      })
    );
  }
}

