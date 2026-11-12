import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Carrito, DireccionCliente } from './models';

@Injectable({
  providedIn: 'root',
})
export class CheckoutService {
  private readonly baseUrl = `${environment.apiUrl}/checkout`;
  private readonly carritoUrl = `${environment.apiUrl}/carrito`;

  constructor(private readonly http: HttpClient) {}

  // Carrito
  getCarrito(): Observable<Carrito> {
    return this.http.get<Carrito>(this.carritoUrl);
  }

  agregarAlCarrito(varianteId: string, cantidad: number): Observable<Carrito> {
    return this.http.post<Carrito>(`${this.carritoUrl}/items`, {
      variante_id: varianteId,
      cantidad,
    });
  }

  actualizarCantidad(itemId: string, cantidad: number): Observable<Carrito> {
    return this.http.patch<Carrito>(`${this.carritoUrl}/items/${itemId}`, { cantidad });
  }

  eliminarItem(itemId: string): Observable<Carrito> {
    return this.http.delete<Carrito>(`${this.carritoUrl}/items/${itemId}`);
  }

  // Checkout
  listarDirecciones(): Observable<{ items: DireccionCliente[] }> {
    return this.http.get<{ items: DireccionCliente[] }>(`${this.baseUrl}/direcciones`);
  }

  validarCheckout(payload: {
    tipo_entrega: 'envio' | 'recojo';
    direccion_id?: string;
    sucursal_id?: string;
    cupon?: string;
  }): Observable<any> {
    return this.http.post(`${this.baseUrl}/validar`, payload);
  }

  crearOrden(
    payload: {
      tipo_entrega: 'envio' | 'recojo';
      direccion_id?: string;
      sucursal_id?: string;
      cupon?: string;
    },
    idempotencyKey: string
  ): Observable<any> {
    return this.http.post(`${this.baseUrl}/ordenes`, payload, {
      headers: { 'Idempotency-Key': idempotencyKey },
    });
  }

  reintentarPago(ventaId: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/ordenes/${ventaId}/reintentar-pago`, {});
  }

  descargarComprobante(ventaId: string, formato: 'pdf' | 'json' = 'pdf'): Observable<any> {
    if (formato === 'pdf') {
      return this.http.get(`${this.baseUrl}/ventas/${ventaId}/comprobante?format=pdf`, {
        responseType: 'blob',
      });
    }
    return this.http.get(`${this.baseUrl}/ventas/${ventaId}/comprobante`);
  }
}

