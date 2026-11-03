import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  EmpresaCreateRequest,
  EmpresaCreateResponse,
  EmpresaListResponse,
  EmpresaResumen,
  EstadoEmpresaResponse,
  MetricasSaaS,
  MiSuscripcionResponse,
  Plan,
  SuscripcionUpsertRequest,
} from './models';
import { NetworkService } from './network.service';

@Injectable({ providedIn: 'root' })
export class SaasService {
  private readonly http = inject(HttpClient);
  private readonly network = inject(NetworkService);
  private readonly apiUrl = environment.apiUrl;

  getMetricas(): Observable<MetricasSaaS> {
    return this.http
      .get<MetricasSaaS>(`${this.apiUrl}/saas/metricas`)
      .pipe(tap(() => this.network.markOnline()));
  }

  listPlanes(): Observable<Plan[]> {
    return this.http.get<Plan[]>(`${this.apiUrl}/saas/planes`).pipe(tap(() => this.network.markOnline()));
  }

  listEmpresas(filters: {
    search?: string;
    estado?: string;
    plan?: string;
    por_vencer?: boolean;
    page?: number;
    page_size?: number;
  }): Observable<EmpresaListResponse> {
    let params = new HttpParams();
    if (filters.search) params = params.set('search', filters.search);
    if (filters.estado) params = params.set('estado', filters.estado);
    if (filters.plan) params = params.set('plan', filters.plan);
    if (filters.por_vencer) params = params.set('por_vencer', 'true');
    params = params
      .set('page', String(filters.page ?? 1))
      .set('page_size', String(filters.page_size ?? 20));

    return this.http
      .get<EmpresaListResponse>(`${this.apiUrl}/saas/empresas`, { params })
      .pipe(tap(() => this.network.markOnline()));
  }

  getEmpresa(id: string): Observable<EmpresaResumen> {
    return this.http
      .get<EmpresaResumen>(`${this.apiUrl}/saas/empresas/${id}`)
      .pipe(tap(() => this.network.markOnline()));
  }

  createEmpresa(payload: EmpresaCreateRequest): Observable<EmpresaCreateResponse> {
    return this.http
      .post<EmpresaCreateResponse>(`${this.apiUrl}/saas/empresas`, payload)
      .pipe(tap(() => this.network.markOnline()));
  }

  assignSuscripcion(
    empresaId: string,
    payload: SuscripcionUpsertRequest,
  ): Observable<MiSuscripcionResponse> {
    return this.http
      .put<MiSuscripcionResponse>(`${this.apiUrl}/saas/empresas/${empresaId}/suscripcion`, payload)
      .pipe(tap(() => this.network.markOnline()));
  }

  suspenderEmpresa(empresaId: string, motivo: string | null): Observable<EstadoEmpresaResponse> {
    return this.http
      .post<EstadoEmpresaResponse>(`${this.apiUrl}/saas/empresas/${empresaId}/suspender`, {
        motivo,
      })
      .pipe(tap(() => this.network.markOnline()));
  }

  reactivarEmpresa(empresaId: string, motivo: string | null): Observable<EstadoEmpresaResponse> {
    return this.http
      .post<EstadoEmpresaResponse>(`${this.apiUrl}/saas/empresas/${empresaId}/reactivar`, {
        motivo,
      })
      .pipe(tap(() => this.network.markOnline()));
  }

  miSuscripcion(): Observable<MiSuscripcionResponse> {
    return this.http
      .get<MiSuscripcionResponse>(`${this.apiUrl}/mi-suscripcion`)
      .pipe(tap(() => this.network.markOnline()));
  }
}

