import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-04: Verificación de Email y Activación de Cuenta
 */
@Injectable({ providedIn: 'root' })
export class CU04VerificacionEmailController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  verificado = signal(false);

  verificar(token: string): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/auth/verify-email', { token }).pipe(
      tap({
        next: () => {
          this.verificado.set(true);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.error?.detail || 'Token inválido o expirado');
          this.cargando.set(false);
        }
      })
    );
  }
}

