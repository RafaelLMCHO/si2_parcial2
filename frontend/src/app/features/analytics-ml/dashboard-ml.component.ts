import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import {
  CU35DashboardAnaliticoMlController,
  DashboardMlResponse,
} from '../../controller/cu35_dashboard_analitico_ml_controller';

@Component({
  selector: 'app-dashboard-ml',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="p-6 max-w-7xl mx-auto space-y-6">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/reportes/convencionales" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-33: Reportes Convencionales</a>
        <a routerLink="/reportes/ia" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-34: Reporte Predictivo con IA</a>
        <a routerLink="/analytics-ml" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #ecfdf5; color: #047857; text-decoration: none;">CU-35: Dashboard Analítico ML</a>
      </div>

      <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-gray-200 gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-35: Dashboard Analítico Machine Learning con Síntesis TTS</h1>
          <p class="text-sm text-gray-500">
            Modelos de scikit-learn: Regresión Supervisada (Demanda) y K-Means No Supervisado (Segmentación RFM)
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            (click)="cargarDashboard()"
            [disabled]="cargando"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50">
            {{ cargando ? 'Entrenando Modelos...' : 'Actualizar Modelos ML' }}
          </button>
        </div>
      </div>

      <!-- Barra de Síntesis Ejecutiva por Audio (TTS) -->
      <div *ngIf="dashboard" class="bg-gradient-to-r from-blue-900 via-indigo-900 to-purple-900 text-white p-5 rounded-2xl shadow-lg flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-blue-300">Diagnóstico Prescriptivo IA / ML</span>
            <span class="px-2 py-0.5 text-xs bg-blue-500/30 rounded-full text-blue-200 font-semibold">Audio TTS Listo</span>
          </div>
          <p class="text-sm text-blue-100 italic leading-relaxed">
            "{{ dashboard.sintesis_ejecutiva }}"
          </p>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button
            (click)="reproducirAudio()"
            class="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-xs rounded-xl shadow transition flex items-center gap-2">
            🔊 Reproducir Audio Síntesis
          </button>
          <button
            (click)="detenerAudio()"
            class="px-3 py-2.5 bg-white/20 hover:bg-white/30 text-white text-xs rounded-xl transition">
            ⏹️ Detener
          </button>
        </div>
      </div>

      <!-- 1. Sección Supervisada: Predicción de Demanda -->
      <div *ngIf="dashboard" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
          <div>
            <span class="text-xs font-bold text-indigo-600 uppercase tracking-wider">Modelo Supervisado (scikit-learn)</span>
            <h2 class="text-lg font-bold text-gray-900">Proyección de Demanda Futura por Categoría Textil</h2>
          </div>
          <div class="flex items-center gap-3 text-xs text-gray-500">
            <span><strong>R² Promedio:</strong> {{ dashboard.prediccion_demanda.metricas['r2_promedio'] }}</span>
            <span><strong>RMSE:</strong> {{ dashboard.prediccion_demanda.metricas['rmse_promedio'] }} un.</span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            *ngFor="let pred of dashboard.prediccion_demanda.predicciones"
            class="p-4 rounded-xl border border-gray-100 bg-gray-50 hover:bg-indigo-50/40 transition space-y-2">
            <span class="text-xs font-semibold uppercase text-gray-500">{{ pred.categoria_nombre }}</span>
            <div class="flex items-baseline justify-between">
              <span class="text-2xl font-extrabold text-indigo-700">{{ pred.demanda_estimada }}</span>
              <span class="text-xs font-semibold text-gray-500">unidades est.</span>
            </div>
            <div class="text-xs text-gray-500 flex justify-between pt-1 border-t border-gray-200">
              <span>Rango 90% IC:</span>
              <span class="font-medium">[{{ pred.intervalo_inferior }} - {{ pred.intervalo_superior }}]</span>
            </div>
            <div class="flex items-center gap-1.5 text-xs font-semibold">
              <span *ngIf="pred.tendencia === 'creciente'" class="text-emerald-600">📈 Tendencia Creciente</span>
              <span *ngIf="pred.tendencia === 'decreciente'" class="text-red-500">📉 Tendencia Decreciente</span>
              <span *ngIf="pred.tendencia === 'estable'" class="text-blue-500">➡️ Tendencia Estable</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Sección No Supervisada: Segmentación K-Means -->
      <div *ngIf="dashboard" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
          <div>
            <span class="text-xs font-bold text-emerald-600 uppercase tracking-wider">Modelo No Supervisado (scikit-learn)</span>
            <h2 class="text-lg font-bold text-gray-900">Segmentación de Clientes por Algoritmo K-Means (RFM)</h2>
          </div>
          <div class="text-xs text-gray-500">
            <span><strong>Total Analizados:</strong> {{ dashboard.segmentacion_clientes.total_clientes_analizados }} clientes</span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            *ngFor="let seg of dashboard.segmentacion_clientes.segmentos"
            class="p-5 rounded-xl border border-gray-200 bg-white hover:shadow-md transition space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-gray-800 text-base">{{ seg.nombre }}</h3>
              <span class="px-2.5 py-0.5 text-xs font-bold bg-emerald-100 text-emerald-800 rounded-full">
                {{ seg.porcentaje_base }}% de la base
              </span>
            </div>
            <p class="text-xs text-gray-600">{{ seg.descripcion }}</p>
            <div class="grid grid-cols-2 gap-2 p-3 bg-gray-50 rounded-lg text-xs">
              <div>
                <span class="text-gray-500 block">Ticket Promedio</span>
                <span class="font-bold text-gray-800">Bs. {{ seg.ticket_promedio | number:'1.2-2' }}</span>
              </div>
              <div>
                <span class="text-gray-500 block">Frecuencia Media</span>
                <span class="font-bold text-gray-800">{{ seg.frecuencia_promedio }} compras/año</span>
              </div>
            </div>
            <div class="text-xs text-indigo-700 bg-indigo-50 p-2.5 rounded-lg border border-indigo-100">
              <strong>Estrategia Recomendada:</strong> {{ seg.estrategia_recomendada }}
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DashboardMlComponent implements OnInit, OnDestroy {
  private controller = inject(CU35DashboardAnaliticoMlController);

  dashboard: DashboardMlResponse | null = null;
  cargando = false;

  ngOnInit(): void {
    this.cargarDashboard();
  }

  ngOnDestroy(): void {
    this.controller.detenerAudio();
  }

  cargarDashboard(): void {
    this.cargando = true;
    this.controller.consultarDashboardMl().subscribe({
      next: (res) => {
        this.dashboard = res;
        this.cargando = false;
      },
      error: () => (this.cargando = false),
    });
  }

  reproducirAudio(): void {
    if (this.dashboard?.audio_tts_url) {
      this.controller.reproducirAudio(this.dashboard.audio_tts_url);
    }
  }

  detenerAudio(): void {
    this.controller.detenerAudio();
  }
}

