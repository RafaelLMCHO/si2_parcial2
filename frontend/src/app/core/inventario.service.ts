import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, from, map, of, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  DisponibilidadPrendaResponse,
  InventarioListResponse,
} from './models';
import { NetworkService } from './network.service';

@Injectable({
  providedIn: 'root',
})
export class InventarioService {
  private readonly baseUrl = `${environment.apiUrl}/inventario`;
  private readonly dbName = 'FashionStoreOfflineDB';
  private readonly storeName = 'existencias_local';

  constructor(
    private readonly http: HttpClient,
    private readonly network: NetworkService
  ) {}

  listarInventario(params?: {
    sucursal_id?: string;
    prenda_id?: string;
    q?: string;
    solo_bajo_minimo?: boolean;
    page?: number;
    page_size?: number;
  }): Observable<InventarioListResponse> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null) {
          httpParams = httpParams.set(key, String(val));
        }
      });
    }
    return this.http.get<InventarioListResponse>(this.baseUrl, { params: httpParams });
  }

  registrarIngreso(payload: {
    sucursal_id: string;
    items: { variante_id: string; cantidad: number }[];
    motivo: string;
    referencia?: string;
  }): Observable<any> {
    return this.http.post(`${this.baseUrl}/movimientos/ingreso`, payload);
  }

  registrarAjuste(payload: {
    sucursal_id: string;
    variante_id: string;
    cantidad: number;
    motivo: string;
    referencia?: string;
  }): Observable<any> {
    return this.http.post(`${this.baseUrl}/movimientos/ajuste`, payload);
  }

  crearTransferencia(payload: {
    origen_id: string;
    destino_id: string;
    items: { variante_id: string; cantidad: number }[];
    motivo?: string;
  }): Observable<any> {
    return this.http.post(`${this.baseUrl}/transferencias`, payload);
  }

  actualizarParametros(
    inventarioId: string,
    payload: { stock_minimo?: number; ubicacion?: string }
  ): Observable<any> {
    return this.http.patch(`${this.baseUrl}/${inventarioId}/parametros`, payload);
  }

  listarMovimientos(params?: any): Observable<any> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) httpParams = httpParams.set(k, String(v));
      });
    }
    return this.http.get(`${this.baseUrl}/movimientos`, { params: httpParams });
  }

  // -------------------------------------------------------------------------
  // CU-18: Disponibilidad con fallback a IndexedDB
  // -------------------------------------------------------------------------
  consultarDisponibilidad(prendaId: string): Observable<DisponibilidadPrendaResponse> {
    const isOnline = navigator.onLine;

    if (isOnline) {
      return this.http
        .get<DisponibilidadPrendaResponse>(`${environment.apiUrl}/inventario/prendas/${prendaId}/disponibilidad`)
        .pipe(
          tap((resp) => this.guardarEnIndexedDB(prendaId, resp)),
          catchError((err) => {
            console.warn('Fallo petición online, intentando IndexedDB local:', err);
            return from(this.recuperarDeIndexedDB(prendaId));
          })
        );
    } else {
      return from(this.recuperarDeIndexedDB(prendaId));
    }
  }

  private async getDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      request.onupgradeneeded = (event: any) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName, { keyPath: 'prenda_id' });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  private async guardarEnIndexedDB(prendaId: string, data: DisponibilidadPrendaResponse): Promise<void> {
    try {
      const db = await this.getDB();
      const tx = db.transaction(this.storeName, 'readwrite');
      tx.objectStore(this.storeName).put({ ...data, prenda_id: prendaId });
    } catch (e) {
      console.warn('No se pudo guardar en IndexedDB local:', e);
    }
  }

  private async recuperarDeIndexedDB(prendaId: string): Promise<DisponibilidadPrendaResponse> {
    try {
      const db = await this.getDB();
      return new Promise((resolve) => {
        const tx = db.transaction(this.storeName, 'readonly');
        const req = tx.objectStore(this.storeName).get(prendaId);
        req.onsuccess = () => {
          if (req.result) {
            resolve({ ...req.result, es_local: true });
          } else {
            resolve({
              prenda_id: prendaId,
              agotado_en_todas: false,
              actualizado_en: new Date().toISOString(),
              sucursales: [],
              es_local: true,
            });
          }
        };
        req.onerror = () => {
          resolve({
            prenda_id: prendaId,
            agotado_en_todas: false,
            actualizado_en: new Date().toISOString(),
            sucursales: [],
            es_local: true,
          });
        };
      });
    } catch (e) {
      return {
        prenda_id: prendaId,
        agotado_en_todas: false,
        actualizado_en: new Date().toISOString(),
        sucursales: [],
        es_local: true,
      };
    }
  }
}

