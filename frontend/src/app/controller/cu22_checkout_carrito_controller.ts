import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-22: Carrito de Compras y Checkout Omnicanal
 */
@Injectable({ providedIn: 'root' })
export class CU22CheckoutCarritoController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  carrito = signal<any>(null);
  ordenCreada = signal<any>(null);

  cargarCarrito(): Observable<any> {
    this.cargando.set(true);
    return this.http.get<any>('/api/v1/carrito').pipe(
      tap({
        next: (data) => {
          this.carrito.set(data);
          this.cargando.set(false);
        },
        error: (err) => {
          this.error.set(err.message);
          this.cargando.set(false);
        }
      })
    );
  }

  crearOrden(payload: {
    tipo_entrega: 'retiro' | 'envio';
    sucursal_id?: string;
    direccion_envio?: string;
  }): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/checkout/ordenes', payload).pipe(
      tap({
        next: (res) => {
          this.ordenCreada.set(res);
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

