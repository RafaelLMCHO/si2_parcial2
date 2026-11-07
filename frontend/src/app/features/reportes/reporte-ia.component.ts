import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import {
  CU34ReporteGenerativoIaController,
  ReporteIaResponse,
} from '../../controller/cu34_reporte_generativo_ia_controller';

@Component({
  selector: 'app-reporte-ia',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="p-6 max-w-7xl mx-auto space-y-6">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/reportes/convencionales" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-33: Reportes Convencionales</a>
        <a routerLink="/reportes/ia" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #faf5ff; color: #7e22ce; text-decoration: none;">CU-34: Reporte Predictivo con IA</a>
        <a routerLink="/analytics-ml" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-35: Dashboard Analítico ML</a>
      </div>

      <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-gray-200 gap-4">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-bold text-gray-900">CU-34: Reporte Generativo Inteligente con IA</h1>
            <span class="px-2.5 py-0.5 text-xs font-semibold bg-purple-100 text-purple-800 rounded-full">
              Plan Profesional (BR-03)
            </span>
          </div>
          <p class="text-sm text-gray-500">
            Formula preguntas en lenguaje natural sobre datos reales con Whitelist estricta y aislamiento multitenant (BR-08)
          </p>
        </div>
      </div>

      <!-- Barra de Consulta por Texto o Voz -->
      <div class="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-4">
        <label class="block text-sm font-semibold text-gray-700">
          ¿Qué análisis deseas consultar hoy?
        </label>
        <div class="flex items-center gap-2">
          <input
            type="text"
            [(ngModel)]="prompt"
            (keyup.enter)="consultarIa('texto')"
            placeholder="Ej: Mostrame las ventas de septiembre agrupadas por sucursal..."
            class="flex-1 p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none" />

          <!-- Botón Dictado por Voz -->
          <button
            type="button"
            (click)="toggleReconocimientoVoz()"
            [class.bg-red-500]="escuchandoVoz"
            [class.bg-gray-100]="!escuchandoVoz"
            [class.text-white]="escuchandoVoz"
            [class.text-gray-700]="!escuchandoVoz"
            class="p-3 rounded-xl hover:bg-gray-200 transition flex items-center justify-center font-medium text-sm gap-1"
            title="Dictar por voz">
            🎙️ {{ escuchandoVoz ? 'Escuchando...' : 'Voz' }}
          </button>

          <!-- Botón Enviar Consulta -->
          <button
            type="button"
            (click)="consultarIa('texto')"
            [disabled]="cargando || !prompt.trim()"
            class="px-5 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-xl shadow-sm transition disabled:opacity-50 flex items-center gap-2">
            <span *ngIf="cargando">Procesando...</span>
            <span *ngIf="!cargando">Generar Reporte</span>
          </button>
        </div>

        <!-- Sugerencias de la Whitelist -->
        <div class="flex flex-wrap items-center gap-2 pt-2">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Consultas Autorizadas:</span>
          <button
            *ngFor="let s of sugerenciasWhitelist"
            (click)="seleccionarSugerencia(s)"
            class="text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 px-3 py-1.5 rounded-lg border border-purple-200 transition">
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Alerta de Error -->
      <div *ngIf="errorMsg" class="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
        <strong>Error de consulta:</strong> {{ errorMsg }}
      </div>

      <!-- Resultado Generado por IA -->
      <div *ngIf="reporte" class="space-y-6">
        <!-- Tarjeta de Resumen Ejecutivo -->
        <div class="bg-gradient-to-r from-purple-900 to-indigo-900 text-white p-6 rounded-2xl shadow-lg space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span class="text-xs font-medium uppercase tracking-wider text-purple-300">
                Reporte Generado: {{ reporte.tipo_reporte }}
              </span>
              <h2 class="text-xl font-bold">{{ reporte.titulo }}</h2>
            </div>
            <!-- Acciones de Exportación -->
            <div class="flex items-center gap-2">
              <button
                (click)="exportar('xlsx')"
                [disabled]="exportando"
                class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition shadow flex items-center gap-1.5">
                📊 Descargar Excel (.xlsx)
              </button>
              <button
                (click)="exportar('pdf')"
                [disabled]="exportando"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold text-xs rounded-lg transition shadow flex items-center gap-1.5">
                📄 Descargar PDF (.pdf)
              </button>
            </div>
          </div>
          <div class="bg-white/10 p-4 rounded-xl backdrop-blur-sm text-sm text-purple-100 leading-relaxed">
            <span class="font-bold text-white">Diagnóstico Ejecutivo:</span> {{ reporte.resumen_ejecutivo }}
          </div>
        </div>

        <!-- KPIs Dinámicos -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4" *ngIf="reporte.kpis">
          <div *ngFor="let k of reporte.kpis | keyvalue" class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <span class="text-xs font-medium text-gray-500 uppercase">{{ formatearClave(k.key) }}</span>
            <div class="mt-1 text-xl font-bold text-gray-800">{{ k.value }}</div>
          </div>
        </div>

        <!-- Visualización de Gráficos de Barra Interactivo -->
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-3">
          <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider">Visualización Gráfica</h3>
          <div class="space-y-2">
            <div *ngFor="let item of reporte.filas; let idx = index" class="space-y-1">
              <div class="flex justify-between text-xs text-gray-600">
                <span class="font-medium">{{ obtenerEtiquetaFila(item) }}</span>
                <span class="font-bold text-purple-700">{{ obtenerValorFila(item) | number:'1.0-2' }}</span>
              </div>
              <div class="w-full bg-gray-100 h-3 rounded-full overflow-hidden">
                <div
                  class="bg-purple-600 h-3 rounded-full transition-all duration-500"
                  [style.width.%]="calcularPorcentajeBarra(item)"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tabla Estructurada -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div class="p-4 border-b border-gray-200 font-semibold text-sm text-gray-700">
            Datos Tabulados Reales
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-gray-700">
              <thead class="bg-gray-50 border-b border-gray-200 text-xs font-semibold uppercase text-gray-600">
                <tr>
                  <th *ngFor="let col of reporte.columnas" class="p-3">{{ col }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr *ngFor="let fila of reporte.filas" class="hover:bg-gray-50">
                  <td *ngFor="let val of fila | keyvalue" class="p-3">
                    {{ val.value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ReporteIaComponent {
  private controller = inject(CU34ReporteGenerativoIaController);

  prompt = '';
  cargando = false;
  exportando = false;
  escuchandoVoz = false;
  errorMsg = '';
  reporte: ReporteIaResponse | null = null;

  sugerenciasWhitelist = [
    'Mostrame las ventas de septiembre agrupadas por sucursal',
    '¿Cuáles fueron los diez productos más vendidos?',
    'Generá un gráfico de ventas por semana',
    'Rotación y stock crítico por categoría',
  ];

  seleccionarSugerencia(s: string): void {
    this.prompt = s;
    this.consultarIa('texto');
  }

  consultarIa(canal: 'texto' | 'voz'): void {
    if (!this.prompt.trim()) return;
    this.cargando = true;
    this.errorMsg = '';
    this.controller.solicitarReporteIa({ prompt: this.prompt, canal }).subscribe({
      next: (res) => {
        this.reporte = res;
        this.cargando = false;
      },
      error: (err) => {
        this.errorMsg = err.error?.detail || 'Error al procesar consulta con el servicio IA';
        this.cargando = false;
      },
    });
  }

  toggleReconocimientoVoz(): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Tu navegador no soporta Web Speech API para dictado por voz.');
      return;
    }

    if (this.escuchandoVoz) {
      this.escuchandoVoz = false;
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.interimResults = false;
    this.escuchandoVoz = true;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      this.prompt = transcript;
      this.escuchandoVoz = false;
      this.consultarIa('voz');
    };

    recognition.onerror = () => {
      this.escuchandoVoz = false;
    };

    recognition.onend = () => {
      this.escuchandoVoz = false;
    };

    recognition.start();
  }

  exportar(formato: 'xlsx' | 'pdf'): void {
    if (!this.reporte) return;
    this.exportando = true;
    this.controller
      .exportarReporte({
        consulta_id: this.reporte.consulta_id,
        tipo_reporte: this.reporte.tipo_reporte,
        formato,
        titulo: this.reporte.titulo,
        resumen: this.reporte.resumen_ejecutivo,
        columnas: this.reporte.columnas,
        filas: this.reporte.filas,
      })
      .subscribe({
        next: (res) => {
          this.exportando = false;
          if (res.contenido_base64) {
            const mime = formato === 'xlsx'
              ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
              : 'application/pdf';
            this.controller.descargarArchivoLocal(
              res.contenido_base64,
              `reporte_${this.reporte?.tipo_reporte}.${formato}`,
              mime
            );
          }
        },
        error: () => (this.exportando = false),
      });
  }

  formatearClave(clave: string): string {
    return clave.replace(/_/g, ' ');
  }

  obtenerEtiquetaFila(fila: Record<string, any>): string {
    const vals = Object.values(fila);
    return String(vals[0] || 'Item');
  }

  obtenerValorFila(fila: Record<string, any>): number {
    const vals = Object.values(fila);
    for (const v of vals) {
      if (typeof v === 'number') return v;
    }
    return 1;
  }

  calcularPorcentajeBarra(fila: Record<string, any>): number {
    if (!this.reporte) return 10;
    const val = this.obtenerValorFila(fila);
    const maxVal = Math.max(...this.reporte.filas.map((f) => this.obtenerValorFila(f)), 1);
    return Math.max(10, Math.min(100, Math.round((val / maxVal) * 100)));
  }
}

