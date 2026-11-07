import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-23: Punto de Venta (POS) - Caja, Venta Rápida y Facturación
 */
@Injectable({ providedIn: 'root' })
export class CU23PuntoVentaPosController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  ultimaVenta = signal<any>(null);

  buscarPorBarcode(codigo: string): Observable<any> {
    return this.http.get<any>(`/api/v1/pos/variantes/barcode/${codigo}`);
  }

  procesarCobro(payload: {
    sucursal_id: string;
    metodo_pago: string;
    monto_recibido: number;
    cliente_nombre?: string;
    cliente_documento?: string;
    lineas: Array<{ variante_id: string; cantidad: number; precio_unitario: number }>;
  }): Observable<any> {
    this.cargando.set(true);
    return this.http.post<any>('/api/v1/pos/ventas', payload).pipe(
      tap({
        next: (res) => {
          this.ultimaVenta.set(res);
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

