import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, of, tap, throwError } from 'rxjs';

import {
  AuxiliaresCatalogoResponse,
  Prenda,
  PrendaListResponse,
} from './models';
import { NetworkService } from './network.service';
import { SessionStoreService } from './session-store.service';

export interface CatalogFilterParams {
  empresa_slug?: string;
  categoria_id?: string;
  temporada_id?: string;
  coleccion_id?: string;
  talla_id?: number;
  color_id?: number;
  precio_min?: number;
  precio_max?: number;
  genero?: string;
  search?: string;
}

export interface CatalogQueryResult {
  items: Prenda[];
  total: number;
  version_catalogo: number;
  isOffline: boolean;
  sinDatosLocales?: boolean;
}

interface OfflineCatalogCache {
  empresa_id?: string;
  version: number;
  updated_at: string;
  items: Prenda[];
}

@Injectable({ providedIn: 'root' })
export class CatalogoService {
  private readonly http = inject(HttpClient);
  private readonly network = inject(NetworkService);
  private readonly sessionStore = inject(SessionStoreService);
  private readonly cacheKey = 'fs_offline_catalog_cache';

  /**
   * CU-13 & CU-14: Consulta de catalogo con filtros y resiliencia offline.
   */
  consultarCatalogo(filters: CatalogFilterParams = {}): Observable<CatalogQueryResult> {
    if (this.network.online()) {
      let params = new HttpParams();
      if (filters.empresa_slug) params = params.set('empresa_slug', filters.empresa_slug);
      if (filters.categoria_id) params = params.set('categoria_id', filters.categoria_id);
      if (filters.temporada_id) params = params.set('temporada_id', filters.temporada_id);
      if (filters.coleccion_id) params = params.set('coleccion_id', filters.coleccion_id);
      if (filters.talla_id) params = params.set('talla_id', filters.talla_id.toString());
      if (filters.color_id) params = params.set('color_id', filters.color_id.toString());
      if (filters.precio_min !== undefined && filters.precio_min !== null) {
        params = params.set('precio_min', filters.precio_min.toString());
      }
      if (filters.precio_max !== undefined && filters.precio_max !== null) {
        params = params.set('precio_max', filters.precio_max.toString());
      }
      if (filters.genero) params = params.set('genero', filters.genero);
      if (filters.search) params = params.set('search', filters.search);

      return this.http.get<PrendaListResponse>('/api/v1/catalogo/prendas', { params }).pipe(
        map((resp) => {
          // Guardar snapshot local para navegacion offline (RNF03)
          this.guardarSnapshotLocal(resp.version_catalogo, resp.items);
          return {
            items: resp.items,
            total: resp.total,
            version_catalogo: resp.version_catalogo,
            isOffline: false,
          };
        }),
        catchError(() => {
          // Si falla la red de forma imprevista, caer a almacenamiento local
          return of(this.consultarOfflineLocal(filters));
        }),
      );
    } else {
      // Modo sin conexion directo
      return of(this.consultarOfflineLocal(filters));
    }
  }

  obtenerAuxiliares(empresa_slug?: string): Observable<AuxiliaresCatalogoResponse> {
    let params = new HttpParams();
    if (empresa_slug) params = params.set('empresa_slug', empresa_slug);
    return this.http.get<AuxiliaresCatalogoResponse>('/api/v1/catalogo/auxiliares', { params }).pipe(
      catchError(() => {
        // En offline, devolver listas maestras vacias o cacheadas
        return of({
          categorias: [],
          colores: [],
          tallas: [],
          temporadas: [],
          colecciones: [],
        });
      }),
    );
  }

  obtenerPrendaPorId(id: string): Observable<Prenda> {
    const isOnline = this.network.online() && (typeof navigator === 'undefined' || navigator.onLine);
    if (!isOnline) {
      const local = this.leerPrendaDesdeCaches(id);
      if (local) {
        return of(local);
      }
      return throwError(() => new Error('Sin conexión y prenda no encontrada en caché local.'));
    }

    return this.http.get<Prenda>(`/api/v1/catalogo/prendas/${id}`).pipe(
      tap((prenda) => this.upsertSnapshotPrenda(prenda)),
      catchError((err) => {
        const local = this.leerPrendaDesdeCaches(id);
        if (local) {
          return of(local);
        }
        return throwError(() => err);
      }),
    );
  }

  obtenerPrendasCacheadas(): Prenda[] {
    return this.leerPrendasOfflineCombinadas();
  }

  private upsertSnapshotPrenda(prenda: Prenda): void {
    if (typeof localStorage === 'undefined' || !prenda?.id) return;
    try {
      const currentEmpresaId = this.sessionStore.readUser()?.empresa_id || prenda.empresa_id || '';
      const raw = localStorage.getItem(this.cacheKey);
      const parsed: OfflineCatalogCache | null = raw ? JSON.parse(raw) : null;
      const cache: OfflineCatalogCache =
        parsed && (!currentEmpresaId || !parsed.empresa_id || parsed.empresa_id === currentEmpresaId)
          ? parsed
          : { empresa_id: currentEmpresaId, version: 1, updated_at: new Date().toISOString(), items: [] };
      const items = Array.isArray(cache.items) ? [...cache.items] : [];
      const idx = items.findIndex((x) => x?.id === prenda.id);
      if (idx >= 0) {
        items[idx] = prenda;
      } else {
        items.push(prenda);
      }
      cache.empresa_id = currentEmpresaId || cache.empresa_id;
      cache.items = items;
      cache.updated_at = new Date().toISOString();
      localStorage.setItem(this.cacheKey, JSON.stringify(cache));
    } catch {
      // Ignorar quota exceeded
    }
  }

  private leerPrendaDesdeCaches(id: string): Prenda | null {
    return this.leerPrendasOfflineCombinadas().find((p) => p.id === id) ?? null;
  }

  private leerPrendasOfflineCombinadas(): Prenda[] {
    if (typeof localStorage === 'undefined') return [];
    const porId = new Map<string, Prenda>();
    const currentEmpresaId = this.sessionStore.readUser()?.empresa_id || '';

    try {
      const raw = localStorage.getItem(this.cacheKey);
      if (raw) {
        const cache: OfflineCatalogCache = JSON.parse(raw);
        const sameTenant = !currentEmpresaId || !cache?.empresa_id || cache.empresa_id === currentEmpresaId;
        if (sameTenant) {
          for (const p of Array.isArray(cache?.items) ? cache.items : []) {
            if (p?.id && (!currentEmpresaId || !p.empresa_id || p.empresa_id === currentEmpresaId)) {
              porId.set(String(p.id), p);
            }
          }
        }
      }
    } catch {
      // Ignorar cache corrupto
    }

    try {
      const cu25Raw = localStorage.getItem('catalogo_offline_cache');
      if (cu25Raw) {
        const cu25 = JSON.parse(cu25Raw);
        const sameTenant = !currentEmpresaId || !cu25?.empresa_id || cu25.empresa_id === currentEmpresaId;
        if (!sameTenant) {
          return Array.from(porId.values());
        }
        const variantesPorPrenda = new Map<string, any[]>();
        for (const v of Array.isArray(cu25?.variantes) ? cu25.variantes : []) {
          const pid = String(v?.prenda_id || '');
          if (!pid) continue;
          const arr = variantesPorPrenda.get(pid) || [];
          arr.push({
            id: String(v.id),
            prenda_id: pid,
            talla_id: Number(v.talla_id || 0),
            talla_nombre: v.talla ?? v.talla_nombre ?? null,
            color_id: Number(v.color_id || 0),
            color_nombre: v.color ?? v.color_nombre ?? null,
            color_hex: v.color_hex ?? null,
            sku: String(v.sku || ''),
            codigo_barras: v.codigo_barras ?? null,
            precio_venta: Number(v.precio_venta || 0),
            costo: Number(v.costo || 0),
            estado: 'activa',
            created_at: '',
            updated_at: '',
          });
          variantesPorPrenda.set(pid, arr);
        }

        for (const p of Array.isArray(cu25?.prendas) ? cu25.prendas : []) {
          const pid = String(p?.id || '');
          if (!pid || porId.has(pid)) continue;
          porId.set(pid, {
            id: pid,
            empresa_id: String(cu25?.empresa_id || ''),
            codigo: String(p.codigo || ''),
            nombre: String(p.nombre || 'Prenda'),
            descripcion: p.descripcion ?? null,
            marca: p.marca ?? null,
            genero: String(p.genero || 'unisex'),
            precio_base: Number(p.precio_base || 0),
            moneda: 'BOB',
            categoria_id: String(p.categoria_id || ''),
            categoria_nombre: p.categoria_nombre ?? null,
            imagen_url: p.imagen_url ?? null,
            estado: 'activa',
            created_at: '',
            updated_at: '',
            variantes: variantesPorPrenda.get(pid) || [],
          });
        }
      }
    } catch {
      // Ignorar cache corrupto
    }

    return Array.from(porId.values());
  }

  private guardarSnapshotLocal(version: number, items: Prenda[]): void {
    if (typeof localStorage === 'undefined') return;
    try {
      const empresaId = this.sessionStore.readUser()?.empresa_id || items[0]?.empresa_id || '';
      const payload: OfflineCatalogCache = {
        empresa_id: empresaId,
        version,
        updated_at: new Date().toISOString(),
        items,
      };
      localStorage.setItem(this.cacheKey, JSON.stringify(payload));
    } catch {
      // Ignorar quota exceeded
    }
  }

  private consultarOfflineLocal(filters: CatalogFilterParams): CatalogQueryResult {
    const items = this.leerPrendasOfflineCombinadas();
    if (items.length === 0) {
      return {
        items: [],
        total: 0,
        version_catalogo: 0,
        isOffline: true,
        sinDatosLocales: true,
      };
    }

    try {
      const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(this.cacheKey) : null;
      const cacheVersion = raw ? (JSON.parse(raw)?.version ?? 1) : 1;
      let filtrados = [...items];

      // Aplicar filtros en memoria local (CU-14 Offline)
      if (filters.categoria_id) {
        filtrados = filtrados.filter((p) => p.categoria_id === filters.categoria_id);
      }
      if (filters.temporada_id) {
        filtrados = filtrados.filter((p) => p.temporada_id === filters.temporada_id);
      }
      if (filters.coleccion_id) {
        filtrados = filtrados.filter((p) => p.coleccion_id === filters.coleccion_id);
      }
      if (filters.genero) {
        filtrados = filtrados.filter((p) => p.genero === filters.genero);
      }
      if (filters.precio_min !== undefined && filters.precio_min !== null) {
        filtrados = filtrados.filter((p) => Number(p.precio_base) >= filters.precio_min!);
      }
      if (filters.precio_max !== undefined && filters.precio_max !== null) {
        filtrados = filtrados.filter((p) => Number(p.precio_base) <= filters.precio_max!);
      }
      if (filters.talla_id) {
        filtrados = filtrados.filter((p) =>
          p.variantes.some((v) => v.talla_id === filters.talla_id),
        );
      }
      if (filters.color_id) {
        filtrados = filtrados.filter((p) =>
          p.variantes.some((v) => v.color_id === filters.color_id),
        );
      }
      if (filters.search) {
        const q = filters.search.toLowerCase().trim();
        filtrados = filtrados.filter(
          (p) =>
            p.nombre.toLowerCase().includes(q) ||
            p.codigo.toLowerCase().includes(q) ||
            (p.marca && p.marca.toLowerCase().includes(q)),
        );
      }

      return {
        items: filtrados,
        total: filtrados.length,
        version_catalogo: cacheVersion,
        isOffline: true,
        sinDatosLocales: false,
      };
    } catch {
      return {
        items: [],
        total: 0,
        version_catalogo: 0,
        isOffline: true,
        sinDatosLocales: true,
      };
    }
  }
}

