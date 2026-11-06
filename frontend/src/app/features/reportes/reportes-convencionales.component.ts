import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  CU33ReportesConvencionalesController,
  DashboardConvencionalResponse,
  RotacionStockResponse,
  TopPrendasResponse,
  VentasPeriodoResponse,
} from '../../controller/cu33_reportes_convencionales_controller';

@Component({
  selector: 'app-reportes-convencionales',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 max-w-7xl mx-auto space-y-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-gray-200 gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-33: Reportes y Dashboards Convencionales</h1>
          <p class="text-sm text-gray-500">Métricas analíticas consolidadas para planes Básico y Profesional</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            (click)="cargarDashboard()"
            [disabled]="cargando"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50">
            {{ cargando ? 'Actualizando...' : 'Actualizar Datos' }}
          </button>
        </div>
      </div>

      <!-- KPIs Principales -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" *ngIf="dashboard">
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <span class="text-xs font-semibold uppercase tracking-wider text-gray-500">Ventas Hoy</span>
          <div class="mt-2 text-2xl font-extrabold text-indigo-600">
            Bs. {{ dashboard.kpis.ventas_hoy | number:'1.2-2' }}
          </div>
        </div>
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <span class="text-xs font-semibold uppercase tracking-wider text-gray-500">Ventas Este Mes</span>
          <div class="mt-2 text-2xl font-extrabold text-emerald-600">
            Bs. {{ dashboard.kpis.ventas_mes | number:'1.2-2' }}
          </div>
        </div>
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <span class="text-xs font-semibold uppercase tracking-wider text-gray-500">Stock Total en Red</span>
          <div class="mt-2 text-2xl font-extrabold text-blue-600">
            {{ dashboard.kpis.stock_total_unidades }} un.
          </div>
        </div>
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <span class="text-xs font-semibold uppercase tracking-wider text-gray-500">Reservas Activas</span>
          <div class="mt-2 text-2xl font-extrabold text-amber-600">
            {{ dashboard.kpis.reservas_activas }}
          </div>
        </div>
      </div>

      <!-- Pestañas de Reporte Específico -->
      <div class="flex border-b border-gray-200 space-x-4">
        <button
          (click)="tabActiva = 'ventas'"
          [class.border-indigo-600]="tabActiva === 'ventas'"
          [class.text-indigo-600]="tabActiva === 'ventas'"
          class="py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700">
          Ventas por Período
        </button>
        <button
          (click)="tabActiva = 'rotacion'"
          [class.border-indigo-600]="tabActiva === 'rotacion'"
          [class.text-indigo-600]="tabActiva === 'rotacion'"
          class="py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700">
          Rotación de Stock
        </button>
        <button
          (click)="tabActiva = 'top'"
          [class.border-indigo-600]="tabActiva === 'top'"
          [class.text-indigo-600]="tabActiva === 'top'"
          class="py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700">
          Top 10 Prendas Más Vendidas
        </button>
      </div>

      <!-- Tab 1: Ventas por Período -->
      <div *ngIf="tabActiva === 'ventas'" class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
        <div class="flex flex-wrap items-center gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-600">Desde</label>
            <input type="date" [(ngModel)]="fechaInicio" class="mt-1 border border-gray-300 rounded-md p-1.5 text-sm" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600">Hasta</label>
            <input type="date" [(ngModel)]="fechaFin" class="mt-1 border border-gray-300 rounded-md p-1.5 text-sm" />
          </div>
          <button
            (click)="consultarVentas()"
            class="mt-5 px-4 py-1.5 bg-gray-800 text-white text-sm rounded-md hover:bg-gray-900">
            Filtrar
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-gray-700">
            <thead class="bg-gray-50 border-b border-gray-200 text-xs font-semibold uppercase text-gray-600">
              <tr>
                <th class="p-3">Período (Día)</th>
                <th class="p-3 text-center">Transacciones</th>
                <th class="p-3 text-right">Monto Total</th>
                <th class="p-3 text-right">Ticket Promedio</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100" *ngIf="ventasData">
              <tr *ngFor="let v of ventasData.items" class="hover:bg-gray-50">
                <td class="p-3 font-medium">{{ v.periodo }}</td>
                <td class="p-3 text-center">{{ v.total_transacciones }}</td>
                <td class="p-3 text-right font-semibold text-emerald-600">Bs. {{ v.monto_total | number:'1.2-2' }}</td>
                <td class="p-3 text-right">Bs. {{ v.ticket_promedio | number:'1.2-2' }}</td>
              </tr>
              <tr *ngIf="ventasData.items.length === 0">
                <td colspan="4" class="p-6 text-center text-gray-400">No hay ventas registradas en el período</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab 2: Rotación de Stock -->
      <div *ngIf="tabActiva === 'rotacion'" class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-800">Rotación de Existencias y Alertas</h2>
          <span class="text-xs font-medium px-2.5 py-1 bg-amber-100 text-amber-800 rounded-full" *ngIf="rotacionData">
            {{ rotacionData.prendas_stock_critico }} prendas con stock crítico (< 5 un.)
          </span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-gray-700">
            <thead class="bg-gray-50 border-b border-gray-200 text-xs font-semibold uppercase text-gray-600">
              <tr>
                <th class="p-3">Código</th>
                <th class="p-3">Prenda</th>
                <th class="p-3">Categoría</th>
                <th class="p-3 text-center">Stock Actual</th>
                <th class="p-3 text-center">Salidas</th>
                <th class="p-3 text-center">Ratio Rotación</th>
                <th class="p-3 text-center">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100" *ngIf="rotacionData">
              <tr *ngFor="let r of rotacionData.items" class="hover:bg-gray-50">
                <td class="p-3 font-mono text-xs">{{ r.codigo }}</td>
                <td class="p-3 font-medium">{{ r.nombre }}</td>
                <td class="p-3">{{ r.categoria }}</td>
                <td class="p-3 text-center font-bold" [class.text-red-600]="r.alerta_stock">{{ r.stock_actual }}</td>
                <td class="p-3 text-center">{{ r.salidas }}</td>
                <td class="p-3 text-center">{{ r.rotacion_ratio | percent }}</td>
                <td class="p-3 text-center">
                  <span *ngIf="r.alerta_stock" class="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full font-semibold">
                    Crítico
                  </span>
                  <span *ngIf="!r.alerta_stock" class="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-700 rounded-full">
                    Normal
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab 3: Top Prendas -->
      <div *ngIf="tabActiva === 'top'" class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
        <h2 class="text-base font-semibold text-gray-800">Ranking Top 10 Prendas Más Vendidas</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-gray-700">
            <thead class="bg-gray-50 border-b border-gray-200 text-xs font-semibold uppercase text-gray-600">
              <tr>
                <th class="p-3 text-center">#</th>
                <th class="p-3">Código</th>
                <th class="p-3">Prenda</th>
                <th class="p-3">Categoría</th>
                <th class="p-3 text-center">Unidades Vendidas</th>
                <th class="p-3 text-right">Ingresos Generados</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100" *ngIf="topPrendasData">
              <tr *ngFor="let tp of topPrendasData.items" class="hover:bg-gray-50">
                <td class="p-3 text-center font-bold text-gray-500">{{ tp.ranking }}</td>
                <td class="p-3 font-mono text-xs">{{ tp.codigo }}</td>
                <td class="p-3 font-medium">{{ tp.nombre }}</td>
                <td class="p-3">{{ tp.categoria }}</td>
                <td class="p-3 text-center font-semibold text-blue-600">{{ tp.cantidad_vendida }}</td>
                <td class="p-3 text-right font-bold text-emerald-600">Bs. {{ tp.total_ingresos | number:'1.2-2' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class ReportesConvencionalesComponent implements OnInit {
  private controller = inject(CU33ReportesConvencionalesController);

  dashboard: DashboardConvencionalResponse | null = null;
  ventasData: VentasPeriodoResponse | null = null;
  rotacionData: RotacionStockResponse | null = null;
  topPrendasData: TopPrendasResponse | null = null;

  tabActiva: 'ventas' | 'rotacion' | 'top' = 'ventas';
  cargando = false;
  fechaInicio = '';
  fechaFin = '';

  ngOnInit(): void {
    this.cargarDashboard();
    this.consultarVentas();
    this.consultarRotacion();
    this.consultarTop();
  }

  cargarDashboard(): void {
    this.cargando = true;
    this.controller.obtenerDashboard().subscribe({
      next: (res) => {
        this.dashboard = res;
        this.cargando = false;
      },
      error: () => (this.cargando = false),
    });
  }

  consultarVentas(): void {
    this.controller
      .consultarVentasPeriodo({ fecha_inicio: this.fechaInicio, fecha_fin: this.fechaFin })
      .subscribe((res) => (this.ventasData = res));
  }

  consultarRotacion(): void {
    this.controller.consultarRotacionStock().subscribe((res) => (this.rotacionData = res));
  }

  consultarTop(): void {
    this.controller.consultarTopPrendas(10).subscribe((res) => (this.topPrendasData = res));
  }
}

