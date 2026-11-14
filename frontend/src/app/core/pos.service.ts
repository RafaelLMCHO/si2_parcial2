import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { PosVentaResponse } from './models';

/**
 * Punto de integración para CU-28 (Venta de Contado Offline).
 */
export interface VentaOfflineHandler {
  registrar(ventaLocal: any, uuid: string): Promise<boolean>;
}

@Injectable({
  providedIn: 'root',
})
export class PosService {
  private readonly baseUrl = `${environment.apiUrl}/pos`;

  // Stub para derivar a modo offline CU-28
  private offlineHandler: VentaOfflineHandler = {
    registrar: async (ventaLocal, uuid) => {
      console.warn(
        `[CU-28] Venta POS derivada a la cola offline local (solo efectivo). UUID: ${uuid}.`,
        ventaLocal
      );
      return true;
    },
  };

  constructor(private readonly http: HttpClient) {}

  buscarPorBarcode(codigo: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/variantes/barcode/${encodeURIComponent(codigo)}`);
  }

  buscarVariantes(q?: string, page: number = 1): Observable<any> {
    let params = new HttpParams().set('page', page);
    if (q) params = params.set('q', q);
    return this.http.get(`${this.baseUrl}/variantes/buscar`, { params });
  }

  registrarVenta(
    payload: {
      idempotency_key: string;
      items: { variante_id: string; cantidad: number; descuento_linea?: number }[];
      cliente: { tipo: 'consumidor_final' | 'identificado'; nombre?: string; documento?: string };
      pago: { metodo: 'efectivo' | 'tarjeta' | 'qr'; monto_recibido?: number; referencia?: string };
    },
    deviceSerial?: string
  ): Observable<PosVentaResponse> {
    let headers = new HttpHeaders();
    if (deviceSerial) {
      headers = headers.set('X-Device-Serial', deviceSerial);
    }

    return this.http.post<PosVentaResponse>(`${this.baseUrl}/ventas`, payload, { headers }).pipe(
      catchError((err) => {
        // Flujo 5.a: Corte imprevisto de red durante el cobro
        if (!navigator.onLine || err.status === 0) {
          if (payload.pago.metodo === 'efectivo') {
            this.offlineHandler.registrar(payload, payload.idempotency_key);
            return throwError(() => ({
              offline: true,
              message: 'Sin conexión: la venta continuará en modo contado offline (CU-28).',
            }));
          } else {
            return throwError(() => ({
              offline: false,
              message: 'Sin conexión: los pagos con tarjeta o QR requieren conexión activa.',
            }));
          }
        }
        return throwError(() => err);
      })
    );
  }

  imprimirTicket(ventaId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/ventas/${ventaId}/ticket`);
  }
}

