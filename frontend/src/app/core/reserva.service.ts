import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, map, of, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  CU26RegistrarReservaOfflineController,
  ReservaOfflineItemPayload,
  generarUuidV4,
} from '../controller/cu26_registrar_reserva_offline_controller';
import { Reserva } from './models';
import { NetworkService } from './network.service';

export interface CrearReservaPayload {
  sucursal_id: string;
  sucursal_nombre?: string | null;
  fecha_visita: string;
  probador?: boolean;
  items: ReservaOfflineItemPayload[];
}

export type ReservaResultado = Reserva & {
  offline?: boolean;
  message?: string;
};

@Injectable({
  providedIn: 'root',
})
export class ReservaService {
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  constructor(
    private readonly http: HttpClient,
    private readonly network: NetworkService,
    private readonly cu26: CU26RegistrarReservaOfflineController,
  ) {}

  validarReserva(payload: {
    sucursal_id: string;
    fecha_visita: string;
    items: { variante_id: string; cantidad: number }[];
  }): Observable<{ ok: boolean }> {
    return this.http.post<{ ok: boolean }>(`${this.baseUrl}/validar`, payload);
  }

  crearReserva(payload: CrearReservaPayload, idempotencyKey?: string): Observable<ReservaResultado> {
    const key = idempotencyKey || generarUuidV4();
    const offlineAhora =
      !this.network.online() || (typeof navigator !== 'undefined' && !navigator.onLine);

    if (offlineAhora) {
      return of(this.encolarReservaOffline(payload));
    }

    const requestBody = {
      sucursal_id: payload.sucursal_id,
      fecha_visita: payload.fecha_visita,
      items: payload.items.map((it) => ({
        variante_id: it.variante_id,
        cantidad: Number(it.cantidad || 1),
      })),
    };

    return this.http
      .post<Reserva>(this.baseUrl, requestBody, {
        headers: { 'Idempotency-Key': key },
      })
      .pipe(
        catchError((err) => {
          const esFalloRed =
            !this.network.online() ||
            (typeof navigator !== 'undefined' && !navigator.onLine) ||
            err?.status === 0 ||
            err?.status === 502 ||
            err?.status === 503 ||
            err?.status === 504;
          if (esFalloRed) {
            return of(this.encolarReservaOffline(payload));
          }
          return throwError(() => err);
        }),
      );
  }

  private encolarReservaOffline(payload: CrearReservaPayload): ReservaResultado {
    const uuid = this.cu26.registrarReserva({
      sucursal_id: payload.sucursal_id,
      sucursal_nombre: payload.sucursal_nombre ?? null,
      fecha_visita: payload.fecha_visita,
      probador: Boolean(payload.probador ?? true),
      items: payload.items,
    });
    const codigoLocal = `RES-OFF-${uuid.slice(0, 8).toUpperCase()}`;

    return {
      id: uuid,
      empresa_id: '',
      usuario_id: '',
      sucursal_id: payload.sucursal_id,
      sucursal_nombre: payload.sucursal_nombre || 'Sucursal seleccionada (Local)',
      codigo: codigoLocal,
      estado: 'pendiente_sync',
      fecha_visita: payload.fecha_visita,
      expira_en: new Date(Date.now() + 24 * 3600 * 1000).toISOString(),
      probador: payload.probador ? 'Por asignar (Offline)' : null,
      items: payload.items.map((it) => ({
        variante_id: it.variante_id,
        sku: it.sku || '',
        prenda_nombre: it.prenda_nombre || 'Prenda reservada (Offline)',
        talla: it.talla || '-',
        color: it.color || '-',
        cantidad: Number(it.cantidad || 1),
      })),
      created_at: new Date().toISOString(),
      offline: true,
      message: `Sin conexión: reserva guardada localmente (${codigoLocal}) y se sincronizará al recuperar la red.`,
    };
  }

  obtenerReservasOfflineLocales(): ReservaResultado[] {
    const ops = this.cu26.listarPendientes();
    return ops.map((op) => {
      const p = op.payload || {};
      const itemsRaw = Array.isArray(p.items) ? p.items : [];
      const codigo = op.codigo_local || p.codigo_local || `RES-OFF-${String(op.id).slice(0, 8).toUpperCase()}`;
      return {
        id: String(op.id),
        empresa_id: '',
        usuario_id: '',
        sucursal_id: String(op.sucursal_id || p.sucursal_id || ''),
        sucursal_nombre: op.sucursal_nombre || p.sucursal_nombre || String(op.sucursal_id || p.sucursal_id || ''),
        codigo,
        estado: op.estado === 'en_conflicto' ? 'conflicto_sync' : 'pendiente_sync',
        fecha_visita: String(p.fecha_visita || op.creada_en || new Date().toISOString()),
        expira_en: String(p.fecha_visita || op.creada_en || new Date().toISOString()),
        probador: p.probador ? 'Por asignar (Offline)' : null,
        items: itemsRaw.map((it: any) => ({
          variante_id: String(it.variante_id || ''),
          sku: String(it.sku || ''),
          prenda_nombre: String(it.prenda_nombre || 'Prenda reservada (Offline)'),
          talla: String(it.talla || '-'),
          color: String(it.color || '-'),
          cantidad: Number(it.cantidad || 1),
        })),
        created_at: String(op.creada_en || new Date().toISOString()),
        offline: true,
        message: op.ultimo_error ? String(op.ultimo_error) : undefined,
      };
    });
  }

  obtenerMisReservas(params?: {
    estado?: string;
    page?: number;
    page_size?: number;
  }): Observable<{ total: number; items: ReservaResultado[] }> {
    const locales = this.obtenerReservasOfflineLocales();
    const offlineAhora =
      !this.network.online() || (typeof navigator !== 'undefined' && !navigator.onLine);
    if (offlineAhora) {
      return of({ total: locales.length, items: locales });
    }

    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) httpParams = httpParams.set(k, String(v));
      });
    }
    return this.http
      .get<{ total: number; items: Reserva[] }>(`${this.baseUrl}/mis-reservas`, {
        params: httpParams,
      })
      .pipe(
        map((resp) => ({
          total: (resp.total ?? resp.items.length) + locales.length,
          items: [...locales, ...(resp.items || [])],
        })),
        catchError((err) => {
          if (!this.network.online() || err?.status === 0) {
            return of({ total: locales.length, items: locales });
          }
          return throwError(() => err);
        }),
      );
  }

  completarReserva(id: string): Observable<Reserva> {
    return this.http.post<Reserva>(`${this.baseUrl}/${id}/completar`, {});
  }

  listarReservas(params?: {
    estado?: string;
    sucursal_id?: string;
    page?: number;
    page_size?: number;
  }): Observable<{ total: number; items: ReservaResultado[] }> {
    const locales = this.obtenerReservasOfflineLocales();
    const offlineAhora =
      !this.network.online() || (typeof navigator !== 'undefined' && !navigator.onLine);
    if (offlineAhora) {
      return of({ total: locales.length, items: locales });
    }

    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) httpParams = httpParams.set(k, String(v));
      });
    }
    return this.http.get<{ total: number; items: Reserva[] }>(this.baseUrl, { params: httpParams }).pipe(
      map((resp) => ({
        total: (resp.total ?? resp.items.length) + locales.length,
        items: [...locales, ...(resp.items || [])],
      })),
      catchError((err) => {
        if (!this.network.online() || err?.status === 0) {
          return of({ total: locales.length, items: locales });
        }
        return throwError(() => err);
      }),
    );
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
    if (this.cu26.esReservaLocal(id)) {
      this.cu26.cancelarReservaLocal(id);
      return of({
        id,
        empresa_id: '',
        usuario_id: '',
        sucursal_id: '',
        codigo: `RES-OFF-${id.slice(0, 8).toUpperCase()}`,
        estado: 'cancelada',
        fecha_visita: new Date().toISOString(),
        expira_en: new Date().toISOString(),
        items: [],
        created_at: new Date().toISOString(),
      });
    }
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

