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
  // CU-18: Disponibilidad con fallback a IndexedDB y caché CU-25
  // -------------------------------------------------------------------------
  consultarDisponibilidad(prendaId: string): Observable<DisponibilidadPrendaResponse> {
    const isOnline = this.network.online() && (typeof navigator === 'undefined' || navigator.onLine);

    if (isOnline) {
      return this.http
        .get<DisponibilidadPrendaResponse>(`${environment.apiUrl}/inventario/prendas/${prendaId}/disponibilidad`)
        .pipe(
          tap((resp) => {
            void this.guardarEnIndexedDB(prendaId, resp);
            this.guardarSucursalesVistas(resp.sucursales || []);
          }),
          catchError((err) => {
            console.warn('Fallo petición online, intentando caché offline local:', err);
            return from(this.recuperarDisponibilidadOffline(prendaId));
          })
        );
    } else {
      return from(this.recuperarDisponibilidadOffline(prendaId));
    }
  }

  obtenerSucursalesOffline(): Array<{
    id: string;
    nombre: string;
    direccion: string;
    ciudad: string;
    es_matriz?: boolean;
  }> {
    const porId = new Map<string, { id: string; nombre: string; direccion: string; ciudad: string; es_matriz?: boolean }>();
    if (typeof localStorage === 'undefined') {
      return [];
    }

    const agregar = (list: any[]) => {
      for (const s of list) {
        if (!s) continue;
        const id = String(s.id || s.sucursal_id || '').trim();
        if (!id || porId.has(id)) continue;
        porId.set(id, {
          id,
          nombre: String(s.nombre || id),
          direccion: String(s.direccion || ''),
          ciudad: String(s.ciudad || ''),
          es_matriz: Boolean(s.es_matriz),
        });
      }
    };

    try {
      const cu25Raw = localStorage.getItem('catalogo_offline_cache');
      if (cu25Raw) {
        const cu25 = JSON.parse(cu25Raw);
        if (Array.isArray(cu25?.sucursales)) {
          agregar(cu25.sucursales);
        }
      }
    } catch {
      // Ignorar cache corrupto
    }

    try {
      const seenRaw = localStorage.getItem('fs_sucursales_cache');
      if (seenRaw) {
        const seen = JSON.parse(seenRaw);
        if (Array.isArray(seen)) {
          agregar(seen);
        }
      }
    } catch {
      // Ignorar cache corrupto
    }

    return Array.from(porId.values());
  }

  private guardarSucursalesVistas(sucursales: any[]): void {
    if (typeof localStorage === 'undefined' || !Array.isArray(sucursales) || sucursales.length === 0) {
      return;
    }
    try {
      const actuales = this.obtenerSucursalesOffline();
      const porId = new Map(actuales.map((s) => [s.id, s]));
      for (const s of sucursales) {
        const id = String(s?.sucursal_id || s?.id || '').trim();
        if (!id) continue;
        porId.set(id, {
          id,
          nombre: String(s.nombre || porId.get(id)?.nombre || id),
          direccion: String(s.direccion || porId.get(id)?.direccion || ''),
          ciudad: String(s.ciudad || porId.get(id)?.ciudad || ''),
          es_matriz: Boolean(s.es_matriz ?? porId.get(id)?.es_matriz),
        });
      }
      localStorage.setItem('fs_sucursales_cache', JSON.stringify(Array.from(porId.values())));
    } catch {
      // Ignorar quota exceeded
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
      if (typeof indexedDB === 'undefined') return;
      const db = await this.getDB();
      const tx = db.transaction(this.storeName, 'readwrite');
      tx.objectStore(this.storeName).put({ ...data, prenda_id: prendaId });
    } catch (e) {
      console.warn('No se pudo guardar en IndexedDB local:', e);
    }
  }

  private leerLocksLocalesActivos(): Map<string, number> {
    const mapLocks = new Map<string, number>();
    if (typeof localStorage === 'undefined') return mapLocks;
    try {
      const raw = JSON.parse(localStorage.getItem('soft_locks_locales') || '[]');
      const now = Date.now();
      for (const l of Array.isArray(raw) ? raw : []) {
        if (!l || new Date(l.expira_en).getTime() <= now) continue;
        const vid = String(l.variante_id || '');
        const sid = String(l.sucursal_id || '');
        const qty = Number(l.cantidad || 0);
        if (!vid || qty <= 0) continue;
        const key = sid ? `${sid}::${vid}` : `ALL::${vid}`;
        mapLocks.set(key, (mapLocks.get(key) || 0) + qty);
      }
    } catch {
      // Ignorar
    }
    return mapLocks;
  }

  private aplicarLocksEnDisponibilidad(
    data: DisponibilidadPrendaResponse,
    locks: Map<string, number>,
  ): DisponibilidadPrendaResponse {
    if (locks.size === 0 || !Array.isArray(data.sucursales)) {
      return data;
    }
    const sucursales = data.sucursales.map((s) => ({
      ...s,
      variantes: (s.variantes || []).map((v) => {
        const lockEsp = locks.get(`${s.sucursal_id}::${v.variante_id}`) || 0;
        const lockAll = locks.get(`ALL::${v.variante_id}`) || 0;
        return {
          ...v,
          stock_disponible: Math.max(0, Number(v.stock_disponible || 0) - lockEsp - lockAll),
        };
      }),
    }));
    const agotado =
      sucursales.length > 0 &&
      sucursales.every((s) => s.variantes.length > 0 && s.variantes.every((v) => v.stock_disponible <= 0));
    return { ...data, sucursales, agotado_en_todas: agotado };
  }

  private construirDesdeCatalogoOffline(
    prendaId: string,
    locks: Map<string, number>,
  ): DisponibilidadPrendaResponse {
    const empty: DisponibilidadPrendaResponse = {
      prenda_id: prendaId,
      agotado_en_todas: false,
      actualizado_en: new Date().toISOString(),
      sucursales: [],
      es_local: true,
    };
    if (typeof localStorage === 'undefined') {
      return empty;
    }

    try {
      const cu25Raw = localStorage.getItem('catalogo_offline_cache');
      const cu25 = cu25Raw ? JSON.parse(cu25Raw) : null;
      const sucursalesCache = this.obtenerSucursalesOffline();
      if (sucursalesCache.length === 0) {
        return empty;
      }

      const variantesMap = new Map<string, { id: string; sku: string; talla: string; color: string }>();
      for (const v of Array.isArray(cu25?.variantes) ? cu25.variantes : []) {
        if (String(v?.prenda_id) === prendaId) {
          variantesMap.set(String(v.id), {
            id: String(v.id),
            sku: String(v.sku || ''),
            talla: String(v.talla || v.talla_nombre || 'Única'),
            color: String(v.color || v.color_nombre || 'Estándar'),
          });
        }
      }

      if (variantesMap.size === 0) {
        const catRaw = localStorage.getItem('fs_offline_catalog_cache');
        const cat = catRaw ? JSON.parse(catRaw) : null;
        const prenda = (Array.isArray(cat?.items) ? cat.items : []).find((p: any) => String(p?.id) === prendaId);
        for (const v of Array.isArray(prenda?.variantes) ? prenda.variantes : []) {
          variantesMap.set(String(v.id), {
            id: String(v.id),
            sku: String(v.sku || ''),
            talla: String(v.talla_nombre || v.talla || 'Única'),
            color: String(v.color_nombre || v.color || 'Estándar'),
          });
        }
      }

      const existenciasMap = new Map<string, number>();
      let hayExistenciasPrenda = false;
      for (const ex of Array.isArray(cu25?.existencias) ? cu25.existencias : []) {
        const vid = String(ex?.variante_id || '');
        const sid = String(ex?.sucursal_id || '');
        if (!variantesMap.has(vid) || !sid) continue;
        hayExistenciasPrenda = true;
        existenciasMap.set(`${sid}::${vid}`, Number(ex.stock_disponible || 0));
      }

      const variantesList = Array.from(variantesMap.values());
      const sucursales = sucursalesCache.map((s) => ({
        sucursal_id: s.id,
        nombre: s.nombre,
        direccion: s.direccion,
        ciudad: s.ciudad,
        variantes: variantesList.map((v) => {
          const baseStock = existenciasMap.get(`${s.id}::${v.id}`) ?? 0;
          const locked = (locks.get(`${s.id}::${v.id}`) || 0) + (locks.get(`ALL::${v.id}`) || 0);
          return {
            variante_id: v.id,
            sku: v.sku,
            talla: v.talla,
            color: v.color,
            stock_disponible: Math.max(0, baseStock - locked),
          };
        }),
      }));

      const agotado =
        hayExistenciasPrenda &&
        variantesList.length > 0 &&
        sucursales.every((s) => s.variantes.every((v) => v.stock_disponible <= 0));

      return {
        prenda_id: prendaId,
        agotado_en_todas: agotado,
        actualizado_en: String(cu25?.generado_en || localStorage.getItem('catalogo_last_sync') || new Date().toISOString()),
        sucursales,
        es_local: true,
      };
    } catch {
      return empty;
    }
  }

  private async recuperarDisponibilidadOffline(prendaId: string): Promise<DisponibilidadPrendaResponse> {
    const locks = this.leerLocksLocalesActivos();
    const idbResp = await this.recuperarDeIndexedDB(prendaId);
    if (idbResp.sucursales && idbResp.sucursales.length > 0) {
      return this.aplicarLocksEnDisponibilidad({ ...idbResp, es_local: true }, locks);
    }
    return this.construirDesdeCatalogoOffline(prendaId, locks);
  }

  private async recuperarDeIndexedDB(prendaId: string): Promise<DisponibilidadPrendaResponse> {
    try {
      if (typeof indexedDB === 'undefined') {
        return {
          prenda_id: prendaId,
          agotado_en_todas: false,
          actualizado_en: new Date().toISOString(),
          sucursales: [],
          es_local: true,
        };
      }
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

