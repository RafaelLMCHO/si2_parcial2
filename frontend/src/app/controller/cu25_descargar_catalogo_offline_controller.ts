import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

/**
 * Controlador Web para CU-25: Descargar Catálogo Offline (IndexedDB / LocalStorage)
 */
@Injectable({ providedIn: 'root' })
export class CU25DescargarCatalogoOfflineController {
  private http = inject(HttpClient);
  cargando = signal(false);
  error = signal<string | null>(null);
  ultimaDescarga = signal<Date | null>(null);
  articulosDescargados = signal<number>(0);

  descargarCatalogo(sucursalId?: string): Observable<any> {
    this.cargando.set(true);
    this.error.set(null);

    const params: any = {};
    if (sucursalId) params.sucursal_id = sucursalId;

    return this.http.get<any>('/api/v1/sync/catalogo-offline', { params }).pipe(
      tap({
        next: (data) => {
          this.cargando.set(false);
          this.articulosDescargados.set(data.total_articulos || 0);
          this.ultimaDescarga.set(new Date());
          localStorage.setItem('catalogo_offline_cache', JSON.stringify(data));
          localStorage.setItem('catalogo_last_sync', new Date().toISOString());
        },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err.message || 'Error al descargar catálogo offline');
        }
      })
    );
  }
}

