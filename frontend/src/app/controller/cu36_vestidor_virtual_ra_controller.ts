import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PrendaArResponse {
  id: string;
  prenda_id: string;
  codigo_prenda: string;
  nombre_prenda: string;
  marca?: string;
  categoria?: string;
  modelo_url: string;
  textura_url?: string;
  puntos_ajuste: Record<string, any>;
  talla_referencia?: string;
  activo: boolean;
}

export interface AvatarClienteDto {
  id: string;
  usuario_id: string;
  nombre: string;
  modelo_url?: string;
  altura_cm?: number;
  peso_kg?: number;
  tono_piel?: string;
  medidas: Record<string, number>;
}

export interface IniciarSesionArResponse {
  sesion_id: string;
  prenda_ar: PrendaArResponse;
  avatar?: AvatarClienteDto;
  estado: string;
  iniciada_en: string;
}

@Injectable({ providedIn: 'root' })
export class CU36VestidorVirtualRaController {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/vestidor';

  listarPrendasAr(): Observable<PrendaArResponse[]> {
    return this.http.get<PrendaArResponse[]>(`${this.baseUrl}/prendas`);
  }

  obtenerPrendaAr(prendaId: string): Observable<PrendaArResponse> {
    return this.http.get<PrendaArResponse>(`${this.baseUrl}/prendas/${prendaId}`);
  }

  obtenerAvatarUsuario(): Observable<AvatarClienteDto> {
    return this.http.get<AvatarClienteDto>(`${this.baseUrl}/avatar`);
  }

  iniciarSesionPrueba(payload: {
    prenda_id: string;
    variante_id?: string;
    avatar_id?: string;
  }): Observable<IniciarSesionArResponse> {
    return this.http.post<IniciarSesionArResponse>(`${this.baseUrl}/sesiones`, payload);
  }

  finalizarSesionPrueba(
    sesionId: string,
    payload: { estado: string; resultado_url?: string }
  ): Observable<{ status: string; sesion_id: string; estado: string }> {
    return this.http.put<{ status: string; sesion_id: string; estado: string }>(
      `${this.baseUrl}/sesiones/${sesionId}`,
      payload
    );
  }
}

