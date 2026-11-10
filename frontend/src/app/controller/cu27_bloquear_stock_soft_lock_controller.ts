import { CommonModule } from '@angular/common';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, catchError, map, of, tap, throwError } from 'rxjs';
import { environment } from '../../environments/environment';

export interface SoftLockItem {
  id: string;
  sucursal_id?: string;
  sucursal_nombre?: string | null;
  variante_id: string;
  sku?: string | null;
  prenda_nombre?: string | null;
  talla?: string | null;
  color?: string | null;
  dispositivo_id?: string;
  cantidad: number;
  expira_en: string;
  creado_en: string;
  ttl_restante_segundos: number;
  activo: boolean;
  origen: 'servidor' | 'local';
}

/**
 * Controlador Web para CU-27: Bloquear Stock Local/Servidor (Soft-Lock) con TTL de 45 minutos
 */
@Injectable({ providedIn: 'root' })
export class CU27BloquearStockSoftLockController {
  private readonly http = inject(HttpClient);
  private readonly storageKey = 'soft_locks_locales';

  cargando = signal(false);
  error = signal<string | null>(null);
  locks = signal<Record<string, number>>({});
  bloqueos = signal<SoftLockItem[]>([]);

  private calcularTtlSegundos(expiraEnIso: string): number {
    const diffMs = new Date(expiraEnIso).getTime() - Date.now();
    return Math.max(0, Math.floor(diffMs / 1000));
  }

  private actualizarSignals(items: SoftLockItem[]): void {
    const vigentes = items
      .map((item) => {
        const ttl = this.calcularTtlSegundos(item.expira_en);
        return {
          ...item,
          ttl_restante_segundos: ttl,
          activo: ttl > 0,
        };
      })
      .filter((item) => item.ttl_restante_segundos > 0);

    const mapCant: Record<string, number> = {};
    for (const item of vigentes) {
      mapCant[item.variante_id] = (mapCant[item.variante_id] || 0) + item.cantidad;
    }

    this.bloqueos.set(vigentes);
    this.locks.set(mapCant);
  }

  cargarLocales(): SoftLockItem[] {
    try {
      const raw = JSON.parse(localStorage.getItem(this.storageKey) || '[]');
      const now = Date.now();
      const vigentes: SoftLockItem[] = (Array.isArray(raw) ? raw : [])
        .filter((l: any) => new Date(l.expira_en).getTime() > now)
        .map((l: any) => ({
          id: String(l.id),
          sucursal_id: l.sucursal_id,
          sucursal_nombre: l.sucursal_nombre ?? null,
          variante_id: String(l.variante_id),
          sku: l.sku ?? null,
          prenda_nombre: l.prenda_nombre ?? null,
          talla: l.talla ?? null,
          color: l.color ?? null,
          dispositivo_id: l.dispositivo_id ?? 'WEB_LOCAL',
          cantidad: Number(l.cantidad || 1),
          expira_en: String(l.expira_en),
          creado_en: String(l.creado_en || new Date().toISOString()),
          ttl_restante_segundos: this.calcularTtlSegundos(String(l.expira_en)),
          activo: true,
          origen: 'local' as const,
        }));

      localStorage.setItem(this.storageKey, JSON.stringify(vigentes));
      this.actualizarSignals(vigentes);
      return vigentes;
    } catch {
      this.actualizarSignals([]);
      return [];
    }
  }

  listarBloqueosActivos(sucursalId?: string): Observable<SoftLockItem[]> {
    this.cargando.set(true);
    this.error.set(null);

    const locales = this.cargarLocales();
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      this.cargando.set(false);
      return of(locales);
    }

    let params = new HttpParams();
    if (sucursalId) {
      params = params.set('sucursal_id', sucursalId);
    }

    return this.http.get<any[]>(`${environment.apiUrl}/sync/soft-locks`, { params }).pipe(
      map((rows) => {
        const servidor: SoftLockItem[] = (Array.isArray(rows) ? rows : []).map((r) => ({
          id: String(r.id),
          sucursal_id: r.sucursal_id ? String(r.sucursal_id) : undefined,
          sucursal_nombre: r.sucursal_nombre ?? null,
          variante_id: String(r.variante_id),
          sku: r.sku ?? null,
          prenda_nombre: r.prenda_nombre ?? null,
          talla: r.talla ?? null,
          color: r.color ?? null,
          dispositivo_id: r.dispositivo_id ?? 'SERVER_DEVICE',
          cantidad: Number(r.cantidad || 1),
          expira_en: String(r.expira_en),
          creado_en: String(r.creado_en || new Date().toISOString()),
          ttl_restante_segundos:
            typeof r.ttl_restante_segundos === 'number'
              ? r.ttl_restante_segundos
              : this.calcularTtlSegundos(String(r.expira_en)),
          activo: r.activo !== false,
          origen: 'servidor' as const,
        }));

        const idsSrv = new Set(servidor.map((s) => s.id));
        const combinados = [...servidor, ...locales.filter((l) => !idsSrv.has(l.id))];
        this.actualizarSignals(combinados);
        this.cargando.set(false);
        return this.bloqueos();
      }),
      catchError(() => {
        this.actualizarSignals(locales);
        this.cargando.set(false);
        return of(locales);
      })
    );
  }

  bloquearStock(
    varianteId: string,
    cantidad: number,
    ttlMinutos: number = 45,
    sucursalId?: string,
    dispositivoId: string = 'WEB_PWA'
  ): boolean {
    this.cargando.set(true);
    this.error.set(null);

    try {
      const expiraEn = new Date(Date.now() + ttlMinutos * 60 * 1000).toISOString();
      const vigentes = this.cargarLocales();
      const nuevoLocal: SoftLockItem = {
        id: 'lock-' + Date.now() + '-' + Math.random().toString(36).substring(2, 6),
        sucursal_id: sucursalId,
        variante_id: varianteId,
        dispositivo_id: dispositivoId,
        cantidad,
        expira_en: expiraEn,
        creado_en: new Date().toISOString(),
        ttl_restante_segundos: ttlMinutos * 60,
        activo: true,
        origen: 'local',
      };

      const activos = [...vigentes, nuevoLocal];
      localStorage.setItem(this.storageKey, JSON.stringify(activos));
      this.actualizarSignals([...this.bloqueos().filter((b) => b.origen === 'servidor'), ...activos]);

      if (sucursalId && (typeof navigator === 'undefined' || navigator.onLine)) {
        this.http
          .post<any>(`${environment.apiUrl}/sync/soft-locks`, {
            sucursal_id: sucursalId,
            variante_id: varianteId,
            cantidad,
            dispositivo_id: dispositivoId,
            ttl_minutos: ttlMinutos,
          })
          .subscribe({
            next: () => {
              this.listarBloqueosActivos(sucursalId).subscribe();
            },
            error: () => {
              // Mantiene el bloqueo local si el endpoint no es accesible offline
            },
          });
      }

      this.cargando.set(false);
      return true;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set('Error aplicando soft-lock local: ' + e.message);
      return false;
    }
  }

  crearBloqueoServidor(payload: {
    sucursal_id: string;
    variante_id: string;
    cantidad: number;
    dispositivo_id?: string;
    ttl_minutos?: number;
  }): Observable<SoftLockItem> {
    this.cargando.set(true);
    this.error.set(null);

    const ttl = payload.ttl_minutos ?? 45;
    const body = {
      sucursal_id: payload.sucursal_id,
      variante_id: payload.variante_id,
      cantidad: payload.cantidad,
      dispositivo_id: payload.dispositivo_id || 'WEB_PWA',
      ttl_minutos: ttl,
    };

    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      this.bloquearStock(body.variante_id, body.cantidad, ttl, body.sucursal_id, body.dispositivo_id);
      const latest = this.bloqueos()[this.bloqueos().length - 1];
      return of(latest);
    }

    return this.http.post<any>(`${environment.apiUrl}/sync/soft-locks`, body).pipe(
      map((res) => {
        const created: SoftLockItem = {
          id: String(res.id),
          sucursal_id: String(res.sucursal_id),
          variante_id: String(res.variante_id),
          dispositivo_id: body.dispositivo_id,
          cantidad: Number(res.cantidad),
          expira_en: String(res.expira_en),
          creado_en: new Date().toISOString(),
          ttl_restante_segundos: this.calcularTtlSegundos(String(res.expira_en)),
          activo: res.activo !== false,
          origen: 'servidor',
        };
        return created;
      }),
      tap(() => {
        this.cargando.set(false);
        this.listarBloqueosActivos().subscribe();
      }),
      catchError((err) => {
        this.cargando.set(false);
        if (err.status === 0) {
          this.bloquearStock(body.variante_id, body.cantidad, ttl, body.sucursal_id, body.dispositivo_id);
          const latest = this.bloqueos()[this.bloqueos().length - 1];
          return of(latest);
        }
        this.error.set(err.error?.detail || 'No se pudo crear el soft-lock');
        return throwError(() => err);
      })
    );
  }

  liberarBloqueo(lock: SoftLockItem | string): Observable<any> {
    const id = typeof lock === 'string' ? lock : lock.id;
    const isLocal = typeof lock === 'string' ? id.startsWith('lock-') : lock.origen === 'local';

    const localesActualizados = this.cargarLocales().filter((l) => l.id !== id);
    localStorage.setItem(this.storageKey, JSON.stringify(localesActualizados));

    if (isLocal) {
      const restantes = this.bloqueos().filter((b) => b.id !== id);
      this.actualizarSignals(restantes);
      return of({ id, liberado: true });
    }

    this.cargando.set(true);
    return this.http.delete<any>(`${environment.apiUrl}/sync/soft-locks/${id}`).pipe(
      tap({
        next: () => {
          this.cargando.set(false);
          this.actualizarSignals(this.bloqueos().filter((b) => b.id !== id));
        },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err.error?.detail || 'No se pudo liberar el bloqueo en servidor');
        },
      })
    );
  }

  refrescarTtlVisual(): void {
    if (this.bloqueos().length > 0) {
      this.actualizarSignals(this.bloqueos());
    }
  }
}
