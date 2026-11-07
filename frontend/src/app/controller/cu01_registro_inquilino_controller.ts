import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-01: Registro de Empresa / Inquilino (Onboarding)
 */
@Injectable({ providedIn: 'root' })
export class CU01RegistroInquilinoController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  mensaje = signal<string | null>(null);

  registrar(data: {
    nombre_empresa: string;
    slug: string;
    nombre_admin: string;
    email_admin: string;
    password: string;
  }): Observable<any> {
    this.cargando.set(true);
    this.error.set(null);
    this.mensaje.set(null);

    return this.http.post<any>('/api/v1/auth/register-tenant', data).pipe(
      tap({
        next: (res) => {
          this.cargando.set(false);
          this.mensaje.set('Empresa registrada con éxito. Revisa el correo de verificación.');
        },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err.error?.detail || 'Error al registrar inquilino');
        }
      })
    );
  }
}

