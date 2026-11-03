import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, of, throwError } from 'rxjs';

import {
  AuxiliaresCatalogoResponse,
  Prenda,
  PrendaListResponse,
} from './models';
import { NetworkService } from './network.service';

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
  version: number;
  updated_at: string;
  items: Prenda[];
}

@Injectable({ providedIn: 'root' })
export class CatalogoService {
  private readonly http = inject(HttpClient);
  private readonly network = inject(NetworkService);
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

  private guardarSnapshotLocal(version: number, items: Prenda[]): void {
    if (typeof localStorage === 'undefined') return;
    try {
      const payload: OfflineCatalogCache = {
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
    if (typeof localStorage === 'undefined') {
      return { items: [], total: 0, version_catalogo: 0, isOffline: true, sinDatosLocales: true };
    }

    const raw = localStorage.getItem(this.cacheKey);
    if (!raw) {
      return {
        items: [],
        total: 0,
        version_catalogo: 0,
        isOffline: true,
        sinDatosLocales: true,
      };
    }

    try {
      const cache: OfflineCatalogCache = JSON.parse(raw);
      let filtrados = [...cache.items];

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
        version_catalogo: cache.version,
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

