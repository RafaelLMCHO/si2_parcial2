import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DemandaPrediccionItem {
  categoria_id?: string;
  categoria_nombre: string;
  periodo: string;
  demanda_estimada: number;
  intervalo_inferior: number;
  intervalo_superior: number;
  tendencia: 'creciente' | 'estable' | 'decreciente';
}

export interface DemandaPrediccionResponse {
  modelo_nombre: string;
  version: string;
  metricas: Record<string, any>;
  predicciones: DemandaPrediccionItem[];
}

export interface SegmentoClienteItem {
  segmento_id: number;
  nombre: string;
  descripcion: string;
  cantidad_clientes: number;
  porcentaje_base: number;
  ticket_promedio: number;
  frecuencia_promedio: number;
  estrategia_recomendada: string;
}

export interface SegmentacionClientesResponse {
  modelo_nombre: string;
  version: string;
  metricas: Record<string, any>;
  total_clientes_analizados: number;
  segmentos: SegmentoClienteItem[];
}

export interface DashboardMlResponse {
  prediccion_demanda: DemandaPrediccionResponse;
  segmentacion_clientes: SegmentacionClientesResponse;
  sintesis_ejecutiva: string;
  audio_tts_url?: string;
  tiene_audio: boolean;
}

export interface SintesisTtsResponse {
  texto: string;
  audio_base64: string;
  mime_type: string;
  duracion_estimada_segundos: number;
}

@Injectable({ providedIn: 'root' })
export class CU35DashboardAnaliticoMlController {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/inteligencia/ml';
  private audioElement: HTMLAudioElement | null = null;

  consultarDashboardMl(): Observable<DashboardMlResponse> {
    return this.http.get<DashboardMlResponse>(`${this.baseUrl}/dashboard`);
  }

  consultarDemanda(): Observable<DemandaPrediccionResponse> {
    return this.http.get<DemandaPrediccionResponse>(`${this.baseUrl}/demanda`);
  }

  consultarSegmentacion(): Observable<SegmentacionClientesResponse> {
    return this.http.get<SegmentacionClientesResponse>(`${this.baseUrl}/segmentacion`);
  }

  solicitarAudioTts(texto: string): Observable<SintesisTtsResponse> {
    return this.http.post<SintesisTtsResponse>(`${this.baseUrl}/sintesis-audio`, { texto });
  }

  reproducirAudio(audioSource: string): void {
    this.detenerAudio();
    this.audioElement = new Audio(audioSource);
    this.audioElement.play().catch((err) => {
      console.warn('Reproducción de audio bloqueada o no disponible:', err);
      // Fallback a SpeechSynthesis del navegador
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance('Diagnóstico ejecutivo completado');
        utterance.lang = 'es-ES';
        window.speechSynthesis.speak(utterance);
      }
    });
  }

  detenerAudio(): void {
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.currentTime = 0;
      this.audioElement = null;
    }
  }
}

