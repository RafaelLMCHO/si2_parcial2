import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

export interface RecomendacionPrenda {
  id: string;
  nombre: string;
  descripcion: string;
  precio_base: number;
  categoria_nombre: string;
  genero: string;
  imagen_url: string;
  tallas_disponibles: string[];
  colores_disponibles: string[];
  rol_en_outfit: string;
  score_afinidad: number;
  por_que_combina: string;
}

export interface OutfitRecomendado {
  titulo_outfit: string;
  estilo: string;
  ocasion: string;
  consejo_estilista_ia: string;
  score_total: number;
  precio_total: number;
  prendas: RecomendacionPrenda[];
  sugerencia_vestidor_prompt: string;
  motor_utilizado: string;
}

@Injectable({
  providedIn: 'root',
})
export class CU38RecomendacionesIaController {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/ia/recomendaciones`;

  // Señales reactivas
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly outfitActual = signal<OutfitRecomendado | null>(null);
  readonly modalAbierto = signal(false);

  recomendarPorPrompt(prompt: string, genero?: string, empresaSlug: string = 'demo'): Observable<OutfitRecomendado> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .post<OutfitRecomendado>(`${this.baseUrl}/estilo-prompt`, {
        prompt,
        genero,
        empresa_slug: empresaSlug,
      })
      .pipe(
        tap({
          next: (res) => {
            this.outfitActual.set(res);
            this.cargando.set(false);
          },
          error: (err) => {
            this.error.set(err?.error?.detail || 'No se pudo generar la recomendación de moda con IA');
            this.cargando.set(false);
          },
        })
      );
  }

  recomendarParaPrenda(prendaId: string, ocasion?: string, empresaSlug: string = 'demo'): Observable<OutfitRecomendado> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .post<OutfitRecomendado>(`${this.baseUrl}/outfit-prenda`, {
        prenda_id: prendaId,
        ocasion,
        empresa_slug: empresaSlug,
      })
      .pipe(
        tap({
          next: (res) => {
            this.outfitActual.set(res);
            this.cargando.set(false);
          },
          error: (err) => {
            this.error.set(err?.error?.detail || 'No se pudo completar el look para esta prenda');
            this.cargando.set(false);
          },
        })
      );
  }

  obtenerTendencias(empresaSlug: string = 'demo', genero?: string): Observable<OutfitRecomendado> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<OutfitRecomendado>(`${this.baseUrl}/tendencias`, {
        params: { empresa_slug: empresaSlug, ...(genero ? { genero } : {}) },
      })
      .pipe(
        tap({
          next: (res) => {
            this.outfitActual.set(res);
            this.cargando.set(false);
          },
          error: (err) => {
            this.error.set(err?.error?.detail || 'No se pudieron cargar las tendencias');
            this.cargando.set(false);
          },
        })
      );
  }

  abrirModal(): void {
    this.modalAbierto.set(true);
  }

  cerrarModal(): void {
    this.modalAbierto.set(false);
  }
}

