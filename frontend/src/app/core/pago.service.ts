import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface IntencionPagoResponse {
  pago_id: string;
  client_secret: string;
  publishable_key: string;
  monto: number;
  moneda: string;
}

export interface EstadoPagoResponse {
  venta_id: string;
  venta_estado: string;
  pago_id?: string;
  pago_estado?: string;
  pasarela_id?: string;
  mensaje_error?: string;
}

@Injectable({
  providedIn: 'root',
})
export class PagoService {
  private readonly baseUrl = `${environment.apiUrl}/pagos`;

  constructor(private readonly http: HttpClient) {}

  crearIntencionPago(ventaId: string, idempotencyKey?: string): Observable<IntencionPagoResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return this.http.post<IntencionPagoResponse>(
      `${this.baseUrl}/intencion`,
      { venta_id: ventaId },
      { headers }
    );
  }

  consultarEstadoPago(ventaId: string): Observable<EstadoPagoResponse> {
    return this.http.get<EstadoPagoResponse>(`${this.baseUrl}/ventas/${ventaId}/estado-pago`);
  }

  getPago(pagoId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/${pagoId}`);
  }
}

