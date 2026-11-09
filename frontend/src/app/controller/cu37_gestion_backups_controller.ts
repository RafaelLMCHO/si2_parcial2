import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface BackupModuloInfo {
  id: string;
  nombre: string;
  descripcion: string;
  tablas: string[];
}

export interface BackupConfiguracion {
  id: string;
  empresa_id: string | null;
  activo: boolean;
  frecuencia: string;
  fecha_inicio: string | null;
  fecha_especifica: string | null;
  hora_ejecucion: string;
  dia_semana: number;
  dia_mes: number;
  destino: string;
  formato: string;
  tablas: string[];
  retencion_dias: number;
  ultima_ejecucion: string | null;
  proxima_ejecucion: string | null;
  estado_ultima_ejecucion: string | null;
  error_ultima_ejecucion: string | null;
}

export interface BackupRegistro {
  id: string;
  empresa_id: string | null;
  empresa_nombre: string | null;
  usuario_id: string | null;
  usuario_nombre: string | null;
  nombre: string;
  descripcion: string | null;
  tipo: 'manual' | 'automatico';
  alcance: 'global' | 'empresa';
  formato: 'json' | 'sql';
  tablas_seleccionadas: string[];
  tamano_bytes: number;
  tamano_legible: string;
  total_registros: number;
  checksum_sha256: string | null;
  guardado_local: boolean;
  ruta_local: string | null;
  guardado_nube: boolean;
  url_nube: string | null;
  proveedor_nube: string;
  estado: string;
  error_mensaje: string | null;
  detalles_tablas: Record<string, number>;
  created_at: string;
}

export interface BackupListResponse {
  items: BackupRegistro[];
  total: number;
  page: number;
  page_size: number;
}

export interface BackupEstadisticas {
  total_backups: number;
  total_locales: number;
  total_nube: number;
  total_automaticos: number;
  total_manuales: number;
  espacio_local_bytes: number;
  espacio_local_legible: string;
  espacio_nube_bytes: number;
  espacio_nube_legible: string;
  proveedor_nube: string;
  ultimo_backup: string | null;
  auto_backup_activo: boolean;
  proximo_auto_backup: string | null;
}

export interface BackupCreateRequest {
  nombre?: string;
  descripcion?: string;
  alcance?: string;
  empresa_id?: string;
  formato?: string;
  destino?: string;
  modulos?: string[];
  tablas?: string[];
  incluir_auditoria?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class CU37GestionBackupsController {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/backups`;

  modulosDisponibles(): Observable<BackupModuloInfo[]> {
    return this.http.get<BackupModuloInfo[]>(`${this.baseUrl}/modulos`);
  }

  obtenerEstadisticas(): Observable<BackupEstadisticas> {
    return this.http.get<BackupEstadisticas>(`${this.baseUrl}/estadisticas`);
  }

  obtenerConfiguracion(): Observable<BackupConfiguracion> {
    return this.http.get<BackupConfiguracion>(`${this.baseUrl}/configuracion`);
  }

  guardarConfiguracion(config: Partial<BackupConfiguracion>): Observable<BackupConfiguracion> {
    return this.http.put<BackupConfiguracion>(`${this.baseUrl}/configuracion`, config);
  }

  ejecutarBackupAuto(): Observable<string[]> {
    return this.http.post<string[]>(`${this.baseUrl}/configuracion/ejecutar-auto`, {});
  }

  listarBackups(filtros: {
    tipo?: string;
    destino?: string;
    search?: string;
    page?: number;
    page_size?: number;
  } = {}): Observable<BackupListResponse> {
    let params = new HttpParams();
    if (filtros.tipo) params = params.set('tipo', filtros.tipo);
    if (filtros.destino) params = params.set('destino', filtros.destino);
    if (filtros.search) params = params.set('search', filtros.search);
    if (filtros.page) params = params.set('page', filtros.page);
    if (filtros.page_size) params = params.set('page_size', filtros.page_size);

    return this.http.get<BackupListResponse>(this.baseUrl, { params });
  }

  crearBackupManual(data: BackupCreateRequest): Observable<BackupRegistro> {
    return this.http.post<BackupRegistro>(this.baseUrl, data);
  }

  obtenerDetalle(backupId: string): Observable<BackupRegistro> {
    return this.http.get<BackupRegistro>(`${this.baseUrl}/${backupId}`);
  }

  descargarArchivo(backupId: string, location: 'local' | 'cloud'): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${backupId}/download/${location}`, {
      responseType: 'blob',
    });
  }

  sincronizarNube(backupId: string): Observable<BackupRegistro> {
    return this.http.post<BackupRegistro>(`${this.baseUrl}/${backupId}/sync-cloud`, {});
  }

  sincronizarLocal(backupId: string): Observable<BackupRegistro> {
    return this.http.post<BackupRegistro>(`${this.baseUrl}/${backupId}/sync-local`, {});
  }

  restaurarBackup(backupId: string, tablas?: string[]): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${backupId}/restaurar`, { tablas });
  }

  eliminarBackup(backupId: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${backupId}`);
  }
}

