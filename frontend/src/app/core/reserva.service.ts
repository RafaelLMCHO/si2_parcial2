import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, of, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { Reserva } from './models';

/**
 * Punto de integración para CU-26 (Registrar reserva offline).
 */
export interface ReservaOfflineHandler {
  registrar(reservaData: any, clienteUuid: string): Promise<boolean>;
}

@Injectable({
  providedIn: 'root',
})
export class ReservaService {
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  // Stub de integración para modo sin conexión (CU-26)
  private offlineHandler: ReservaOfflineHandler = {
    registrar: async (reservaData, clienteUuid) => {
      console.warn(
        `[CU-26 STUB] Reserva encolada offline con UUID: ${clienteUuid}. Se sincronizará al recuperar conexión.`,
        reservaData
      );
      return true;
    },
  };

  constructor(private readonly http: HttpClient) {}

  validarReserva(payload: {
    sucursal_id: string;
    fecha_visita: string;
    items: { variante_id: string; cantidad: number }[];
  }): Observable<{ ok: boolean }> {
    return this.http.post<{ ok: boolean }>(`${this.baseUrl}/validar`, payload);
  }

  crearReserva(
    payload: {
      sucursal_id: string;
      fecha_visita: string;
      probador?: boolean;
      items: { variante_id: string; cantidad: number }[];
    },
    idempotencyKey?: string
  ): Observable<Reserva> {
    const key = idempotencyKey || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2));
    return this.http
      .post<Reserva>(this.baseUrl, payload, {
        headers: { 'Idempotency-Key': key },
      })
      .pipe(
        catchError((err) => {
          // Flujo 4.a: Error de transporte/red -> delegar en hook offline CU-26
          if (!navigator.onLine || err.status === 0) {
            this.offlineHandler.registrar(payload, key);
            return throwError(() => ({
              offline: true,
              message: 'Sin conexión: la reserva se guardó localmente y se registrará al recuperar la red.',
            }));
          }
          return throwError(() => err);
        })
      );
  }

  obtenerMisReservas(params?: {
    estado?: string;
    page?: number;
    page_size?: number;
  }): Observable<{ total: number; items: Reserva[] }> {
    return this.listarReservas(params);
  }

  completarReserva(id: string): Observable<Reserva> {
    return this.http.post<Reserva>(`${this.baseUrl}/${id}/completar`, {});
  }

  listarReservas(params?: {
    estado?: string;
    sucursal_id?: string;
    page?: number;
    page_size?: number;
  }): Observable<{ total: number; items: Reserva[] }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) httpParams = httpParams.set(k, String(v));
      });
    }
    return this.http.get<{ total: number; items: Reserva[] }>(this.baseUrl, { params: httpParams });
  }

  listarPorPreparar(params?: { sucursal_id?: string }): Observable<{ total: number; items: Reserva[] }> {
    let httpParams = new HttpParams();
    if (params?.sucursal_id) httpParams = httpParams.set('sucursal_id', params.sucursal_id);
    return this.http.get<{ total: number; items: Reserva[] }>(`${this.baseUrl}/por-preparar`, { params: httpParams });
  }

  getReserva(id: string): Observable<Reserva> {
    return this.http.get<Reserva>(`${this.baseUrl}/${id}`);
  }

  cancelarReserva(id: string, motivo?: string): Observable<Reserva> {
    return this.http.post<Reserva>(`${this.baseUrl}/${id}/cancelar`, { motivo });
  }

  prepararReserva(id: string, probador?: string): Observable<Reserva> {
    return this.http.post<Reserva>(`${this.baseUrl}/${id}/preparar`, { probador });
  }

  reportarIncidencia(id: string, payload: {
    variante_ids: string[];
    motivo: string;
    registrar_merma?: boolean;
  }): Observable<any> {
    return this.http.post(`${this.baseUrl}/${id}/incidencia`, payload);
  }
}

