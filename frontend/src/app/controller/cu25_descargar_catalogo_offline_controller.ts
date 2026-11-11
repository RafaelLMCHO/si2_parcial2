import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, EMPTY, tap } from 'rxjs';
import { AuthService } from '../core/auth.service';
import { NetworkService } from '../core/network.service';

export interface SucursalOfflineCache {
  id: string;
  nombre: string;
  direccion?: string;
  ciudad?: string;
  es_matriz?: boolean;
}

/**
 * Controlador Web para CU-25: Descargar Catálogo Offline (IndexedDB / LocalStorage)
 */
@Injectable({ providedIn: 'root' })
export class CU25DescargarCatalogoOfflineController {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly network = inject(NetworkService);

  private prefetchInProgress = false;
  private hasPrefetched = false;

  cargando = signal(false);
  error = signal<string | null>(null);
  ultimaDescarga = signal<Date | null>(this.leerFechaCache());
  articulosDescargados = signal<number>(this.leerConteoArticulosCache());
  sucursalesDescargadas = signal<number>(this.obtenerSucursalesCacheadas().length);
  sucursalesList = signal<SucursalOfflineCache[]>(this.obtenerSucursalesCacheadas());

  descargarCatalogo(sucursalId?: string): Observable<any> {
    this.cargando.set(true);
    this.error.set(null);

    const params: any = {};
    if (sucursalId) params.sucursal_id = sucursalId;

    return this.http.get<any>('/api/v1/sync/catalogo-offline', { params }).pipe(
      tap({
        next: (data) => {
          this.cargando.set(false);
          const total = data?.total_articulos ?? (Array.isArray(data?.prendas) ? data.prendas.length : 0);
          const sucursales: SucursalOfflineCache[] = (Array.isArray(data?.sucursales) ? data.sucursales : []).map((s: any) => ({
            id: String(s.id),
            nombre: String(s.nombre || s.id),
            direccion: String(s.direccion || ''),
            ciudad: String(s.ciudad || ''),
            es_matriz: Boolean(s.es_matriz),
          }));
          this.articulosDescargados.set(total);
          this.sucursalesDescargadas.set(sucursales.length);
          this.sucursalesList.set(sucursales);
          this.ultimaDescarga.set(new Date());
          this.hasPrefetched = true;
          if (typeof localStorage !== 'undefined') {
            try {
              const empresaId = data?.empresa_id || this.auth.user()?.empresa_id || '';
              localStorage.setItem('catalogo_offline_cache', JSON.stringify(data));
              localStorage.setItem('catalogo_last_sync', new Date().toISOString());
              if (sucursales.length > 0) {
                localStorage.setItem('fs_sucursales_cache', JSON.stringify({ empresa_id: empresaId, items: sucursales }));
              }
            } catch {
              // Ignorar límite de almacenamiento
            }
          }
        },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err?.message || 'Error al descargar catálogo offline');
        },
      }),
    );
  }

  asegurarCatalogoOfflineCargado(forzar = false): void {
    if (typeof localStorage === 'undefined') return;
    if (!this.network.online() || (typeof navigator !== 'undefined' && !navigator.onLine)) return;
    const user = this.auth.user();
    if (!this.auth.isAuthenticated() || !user?.empresa_id) return;
    if (user.rol === 'superadmin' && !user.empresa_id) return;
    if (this.prefetchInProgress || this.cargando()) return;

    const raw = localStorage.getItem('catalogo_offline_cache');
    let rawCache: any = null;
    try {
      rawCache = raw ? JSON.parse(raw) : null;
    } catch {
      rawCache = null;
    }
    if (rawCache?.empresa_id && rawCache.empresa_id !== user.empresa_id) {
      this.limpiarCacheLocal();
      forzar = true;
    }

    const cache = this.leerCacheLocal();
    const hasSucursales = Array.isArray(cache?.sucursales) && cache.sucursales.length > 0;
    const lastSyncStr = localStorage.getItem('catalogo_last_sync');
    const ageMs = lastSyncStr ? Date.now() - new Date(lastSyncStr).getTime() : Number.POSITIVE_INFINITY;

    if (!forzar && this.hasPrefetched && hasSucursales && ageMs < 5 * 60 * 1000) {
      this.sucursalesList.set(this.obtenerSucursalesCacheadas());
      return;
    }

    this.prefetchInProgress = true;
    this.descargarCatalogo()
      .pipe(catchError(() => EMPTY))
      .subscribe({
        complete: () => {
          this.prefetchInProgress = false;
        },
        error: () => {
          this.prefetchInProgress = false;
        },
      });
  }

  limpiarCacheLocal(): void {
    this.hasPrefetched = false;
    this.sucursalesList.set([]);
    this.sucursalesDescargadas.set(0);
    this.articulosDescargados.set(0);
    this.ultimaDescarga.set(null);
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('catalogo_offline_cache');
      localStorage.removeItem('catalogo_last_sync');
      localStorage.removeItem('fs_sucursales_cache');
      localStorage.removeItem('fs_offline_catalog_cache');
      localStorage.removeItem('soft_locks_locales');
    }
  }

  resetPrefetch(): void {
    this.hasPrefetched = false;
  }

  leerCacheLocal(): any | null {
    if (typeof localStorage === 'undefined') return null;
    try {
      const raw = localStorage.getItem('catalogo_offline_cache');
      const parsed = raw ? JSON.parse(raw) : null;
      const userEmpresaId = this.auth.user()?.empresa_id;
      if (parsed?.empresa_id && userEmpresaId && parsed.empresa_id !== userEmpresaId) {
        return null;
      }
      return parsed;
    } catch {
      return null;
    }
  }

  obtenerSucursalesCacheadas(): SucursalOfflineCache[] {
    const cache = this.leerCacheLocal();
    if (Array.isArray(cache?.sucursales) && cache.sucursales.length > 0) {
      return cache.sucursales.map((s: any) => ({
        id: String(s.id),
        nombre: String(s.nombre || s.id),
        direccion: String(s.direccion || ''),
        ciudad: String(s.ciudad || ''),
        es_matriz: Boolean(s.es_matriz),
      }));
    }
    if (typeof localStorage !== 'undefined') {
      try {
        const raw = localStorage.getItem('fs_sucursales_cache');
        const parsed = raw ? JSON.parse(raw) : null;
        const userEmpresaId = this.auth.user()?.empresa_id;
        if (parsed && !Array.isArray(parsed) && parsed.empresa_id && userEmpresaId && parsed.empresa_id !== userEmpresaId) {
          return [];
        }
        const list = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.items) ? parsed.items : [];
        return list.map((s: any) => ({
          id: String(s.id || s.sucursal_id),
          nombre: String(s.nombre || s.id || s.sucursal_id),
          direccion: String(s.direccion || ''),
          ciudad: String(s.ciudad || ''),
          es_matriz: Boolean(s.es_matriz),
        }));
      } catch {
        return [];
      }
    }
    return [];
  }

  private leerFechaCache(): Date | null {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem('catalogo_last_sync');
    if (!raw) return null;
    const d = new Date(raw);
    return Number.isNaN(d.getTime()) ? null : d;
  }

  private leerConteoArticulosCache(): number {
    const cache = this.leerCacheLocal();
    if (!cache) return 0;
    return Number(cache.total_articulos ?? (Array.isArray(cache.prendas) ? cache.prendas.length : 0));
  }
}

