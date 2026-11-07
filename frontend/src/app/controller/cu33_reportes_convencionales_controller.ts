import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface VentasPeriodoItem {
  periodo: string;
  total_transacciones: number;
  monto_total: number;
  ticket_promedio: number;
}

export interface VentasPeriodoResponse {
  items: VentasPeriodoItem[];
  total_general: number;
  total_operaciones: number;
  ticket_promedio_general: number;
}

export interface RotacionStockItem {
  prenda_id: string;
  codigo: string;
  nombre: string;
  categoria: string;
  stock_actual: number;
  entradas: number;
  salidas: number;
  rotacion_ratio: number;
  alerta_stock: boolean;
}

export interface RotacionStockResponse {
  items: RotacionStockItem[];
  prendas_stock_critico: number;
  stock_total_unidades: number;
}

export interface TopPrendasItem {
  ranking: number;
  prenda_id: string;
  codigo: string;
  nombre: string;
  categoria: string;
  cantidad_vendida: number;
  total_ingresos: number;
}

export interface TopPrendasResponse {
  items: TopPrendasItem[];
  total_prendas_vendidas: number;
  total_ingresos_generados: number;
}

export interface DashboardConvencionalResponse {
  kpis: {
    ventas_hoy: number;
    ventas_mes: number;
    stock_total_unidades: number;
    reservas_activas: number;
  };
  ventas_por_sucursal: Array<{
    sucursal_id: string;
    sucursal_nombre: string;
    total_ventas: number;
    operaciones: number;
  }>;
  top_prendas: TopPrendasItem[];
  rotacion_resumen: {
    stock_critico: number;
    total_unidades: number;
  };
  ventas_tendencia_dias: Array<{ fecha: string; total: number }>;
}

@Injectable({ providedIn: 'root' })
export class CU33ReportesConvencionalesController {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/reportes/convencionales';

  obtenerDashboard(): Observable<DashboardConvencionalResponse> {
    return this.http.get<DashboardConvencionalResponse>(`${this.baseUrl}/dashboard`);
  }

  consultarVentasPeriodo(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    sucursal_id?: string;
  }): Observable<VentasPeriodoResponse> {
    let httpParams = new HttpParams();
    if (params?.fecha_inicio) httpParams = httpParams.set('fecha_inicio', params.fecha_inicio);
    if (params?.fecha_fin) httpParams = httpParams.set('fecha_fin', params.fecha_fin);
    if (params?.sucursal_id) httpParams = httpParams.set('sucursal_id', params.sucursal_id);
    return this.http.get<VentasPeriodoResponse>(`${this.baseUrl}/ventas`, { params: httpParams });
  }

  consultarRotacionStock(params?: {
    categoria_id?: string;
    sucursal_id?: string;
  }): Observable<RotacionStockResponse> {
    let httpParams = new HttpParams();
    if (params?.categoria_id) httpParams = httpParams.set('categoria_id', params.categoria_id);
    if (params?.sucursal_id) httpParams = httpParams.set('sucursal_id', params.sucursal_id);
    return this.http.get<RotacionStockResponse>(`${this.baseUrl}/rotacion`, { params: httpParams });
  }

  consultarTopPrendas(limite = 10): Observable<TopPrendasResponse> {
    const params = new HttpParams().set('limite', limite.toString());
    return this.http.get<TopPrendasResponse>(`${this.baseUrl}/top-prendas`, { params });
  }
}

