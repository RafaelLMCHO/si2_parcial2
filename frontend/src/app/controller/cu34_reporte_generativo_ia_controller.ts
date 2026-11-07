import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ReporteIaRequest {
  prompt: string;
  canal?: 'texto' | 'voz';
  audio_base64?: string;
}

export interface ReporteIaResponse {
  consulta_id: string;
  prompt_recibido: string;
  tipo_reporte: string;
  titulo: string;
  resumen_ejecutivo: string;
  kpis: Record<string, any>;
  columnas: string[];
  filas: Record<string, any>[];
  tipo_grafico: 'barras' | 'lineas' | 'torta' | 'tabla';
  datos_grafico: {
    labels: string[];
    datasets: Array<{ label: string; data: number[] }>;
  };
  parametros_aplicados: Record<string, any>;
  sugerencias: string[];
  permitido_exportar: boolean;
}

export interface ExportarReporteRequest {
  consulta_id?: string;
  tipo_reporte: string;
  formato: 'xlsx' | 'pdf' | 'csv';
  titulo: string;
  resumen?: string;
  columnas: string[];
  filas: Record<string, any>[];
  parametros?: Record<string, any>;
}

export interface ExportarReporteResponse {
  reporte_id: string;
  tipo_reporte: string;
  formato: string;
  archivo_url: string;
  tamano_bytes: number;
  generado_en: string;
  contenido_base64?: string;
}

@Injectable({ providedIn: 'root' })
export class CU34ReporteGenerativoIaController {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/reportes/ia';

  solicitarReporteIa(payload: ReporteIaRequest): Observable<ReporteIaResponse> {
    return this.http.post<ReporteIaResponse>(`${this.baseUrl}/consultar`, payload);
  }

  exportarReporte(payload: ExportarReporteRequest): Observable<ExportarReporteResponse> {
    return this.http.post<ExportarReporteResponse>(`${this.baseUrl}/exportar`, payload);
  }

  descargarArchivoLocal(base64Data: string, filename: string, mimeType: string): void {
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

