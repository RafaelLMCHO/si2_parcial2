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
    <div class="ia-report-page font-sans">
      <div class="subnav-bar">
        <a routerLink="/reportes/convencionales" class="subnav-link">CU-33: Reportes Convencionales</a>
        <a routerLink="/reportes/ia" class="subnav-link active">CU-34: Reporte Predictivo con IA (Voz/Texto)</a>
        <a routerLink="/analytics-ml" class="subnav-link">CU-35: Dashboard Analítico ML</a>
      </div>

      <div class="page-header">
        <div>
          <div class="title-row">
            <h1 class="main-title">CU-34: Reporte Generativo Inteligente con IA</h1>
            <span class="plan-badge">
              Plan Profesional (BR-03)
            </span>
          </div>
          <p class="subtitle">
            Formula preguntas mediante comandos de voz o texto en lenguaje natural sobre datos reales de tu empresa (Whitelist segura BR-08).
          </p>
        </div>
      </div>

      <!-- Barra de Consulta por Texto o Voz -->
      <div class="search-card">
        <label class="search-label">
          ¿Qué análisis deseas consultar hoy? (Escribe o pulsa el micrófono para dictar)
        </label>
        <div class="input-actions-row">
          <input
            type="text"
            [(ngModel)]="prompt"
            (keyup.enter)="consultarIa('texto')"
            placeholder="Ej: Mostrame las ventas de septiembre agrupadas por sucursal..."
            class="prompt-input"
          />

          <!-- Botón Dictado por Voz (Web Speech API) -->
          <button
            type="button"
            (click)="toggleReconocimientoVoz()"
            [class.voice-active]="escuchandoVoz"
            class="btn-voice"
            title="Activar reconocimiento de voz por micrófono"
          >
            @if (escuchandoVoz) {
              <span class="mic-pulse">🔴</span> Escuchando...
            } @else {
              <span>🎙️</span> Dictar Voz
            }
          </button>

          <!-- Botón Enviar Consulta -->
          <button
            type="button"
            (click)="consultarIa('texto')"
            [disabled]="cargando || !prompt.trim()"
            class="btn-submit"
          >
            <span *ngIf="cargando">Procesando...</span>
            <span *ngIf="!cargando">✨ Generar Reporte</span>
          </button>
        </div>

        @if (escuchandoVoz) {
          <div class="voice-listening-banner animate-fade-in">
            <div class="wave-anim"></div>
            <span>Micrófono abierto: Puedes hablar en español ahora (ej. <em>"¿Cuáles fueron los diez productos más vendidos?"</em>)...</span>
          </div>
        }

        <!-- Sugerencias de la Whitelist -->
        <div class="whitelist-box">
          <span class="whitelist-title">Consultas Rápidas Autorizadas:</span>
          <div class="suggestions-list">
            @for (s of sugerenciasWhitelist; track s) {
              <button
                type="button"
                (click)="seleccionarSugerencia(s)"
                class="suggestion-chip"
              >
                {{ s }}
              </button>
            }
          </div>
        </div>
      </div>

      <!-- Alerta de Error -->
      <div *ngIf="errorMsg" class="error-banner animate-fade-in">
        <strong>⚠️ Error:</strong> {{ errorMsg }}
      </div>

      <!-- Resultado Generado por IA -->
      <div *ngIf="reporte" class="results-container animate-fade-in">
        <!-- Tarjeta de Resumen Ejecutivo -->
        <div class="executive-card">
          <div class="executive-header">
            <div>
              <span class="report-type-tag">
                Tipo: {{ reporte.tipo_reporte }} • Canal: {{ canalUtilizado === 'voz' ? '🎙️ Comando de Voz' : '⌨️ Texto' }}
              </span>
              <h2 class="report-title">{{ reporte.titulo }}</h2>
            </div>

            <!-- Acciones de Exportación -->
            <div class="export-actions">
              <button
                type="button"
                (click)="exportar('xlsx')"
                [disabled]="exportando"
                class="btn-export-excel"
              >
                📊 Descargar Excel (.xlsx)
              </button>
              <button
                type="button"
                (click)="exportar('pdf')"
                [disabled]="exportando"
                class="btn-export-pdf"
              >
                📄 Descargar PDF (.pdf)
              </button>
            </div>
          </div>

          <div class="diagnosis-box">
            <strong>Diagnóstico Ejecutivo IA:</strong> {{ reporte.resumen_ejecutivo }}
          </div>
        </div>

        <!-- KPIs Dinámicos -->
        <div class="kpis-grid" *ngIf="reporte.kpis">
          <div *ngFor="let k of reporte.kpis | keyvalue" class="kpi-card">
            <span class="kpi-label">{{ formatearClave(k.key) }}</span>
            <div class="kpi-val">{{ k.value }}</div>
          </div>
        </div>

        <!-- Visualización de Gráficos de Barra Interactivo -->
        <div class="chart-card">
          <h3 class="card-section-title">Visualización Gráfica Comparativa</h3>
          <div class="bars-list">
            <div *ngFor="let item of reporte.filas; let idx = index" class="bar-row">
              <div class="bar-labels">
                <span class="bar-name">{{ obtenerEtiquetaFila(item) }}</span>
                <span class="bar-value">{{ obtenerValorFila(item) | number:'1.0-2' }}</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  [style.width.%]="calcularPorcentajeBarra(item)"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tabla Estructurada -->
        <div class="table-card">
          <div class="table-header">
            Datos Tabulados Reales del Tenant (Aislamiento RLS)
          </div>
          <div class="table-wrapper">
            <table class="report-table">
              <thead>
                <tr>
                  <th *ngFor="let col of reporte.columnas">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let fila of reporte.filas">
                  <td *ngFor="let val of fila | keyvalue">
                    {{ val.value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .ia-report-page {
      padding: 24px;
      max-width: 1200px;
      margin: 0 auto;
      color: #0f172a;
    }
    .subnav-bar {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      background: #ffffff;
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid #e2e8f0;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .subnav-link {
      padding: 8px 14px;
      border-radius: 10px;
      font-size: 0.85rem;
      font-weight: 600;
      color: #64748b;
      text-decoration: none;
      transition: all 0.15s;
    }
    .subnav-link:hover {
      background: #f8fafc;
      color: #0f172a;
    }
    .subnav-link.active {
      background: #f5f3ff;
      color: #7c3aed;
      font-weight: 800;
    }
    .page-header {
      padding-bottom: 16px;
      border-bottom: 1px solid #e2e8f0;
      margin-bottom: 20px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .main-title {
      font-size: 1.6rem;
      font-weight: 900;
      color: #0f172a;
      margin: 0;
    }
    .plan-badge {
      background: #ede9fe;
      color: #6d28d9;
      font-size: 0.72rem;
      font-weight: 800;
      padding: 3px 10px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .subtitle {
      color: #64748b;
      font-size: 0.9rem;
      margin: 6px 0 0 0;
    }
    .search-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.03);
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 24px;
    }
    .search-label {
      font-size: 0.92rem;
      font-weight: 700;
      color: #334155;
    }
    .input-actions-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .prompt-input {
      flex: 1;
      min-width: 280px;
      padding: 12px 16px;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      font-size: 0.9rem;
      outline: none;
    }
    .prompt-input:focus {
      border-color: #7c3aed;
      box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
    }
    .btn-voice {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 12px 18px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #f8fafc;
      color: #334155;
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-voice:hover {
      background: #f1f5f9;
      border-color: #cbd5e1;
    }
    .btn-voice.voice-active {
      background: #ef4444;
      color: #ffffff;
      border-color: #dc2626;
      box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.25);
      animation: pulseRecord 1.2s infinite;
    }
    .btn-submit {
      padding: 12px 24px;
      background: #7c3aed;
      color: #ffffff;
      border: none;
      border-radius: 12px;
      font-size: 0.9rem;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
      transition: all 0.15s;
    }
    .btn-submit:hover:not(:disabled) {
      background: #6d28d9;
    }
    .btn-submit:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .voice-listening-banner {
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 12px;
      padding: 12px 16px;
      color: #991b1b;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .whitelist-box {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-top: 10px;
      border-top: 1px solid #f1f5f9;
    }
    .whitelist-title {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #94a3b8;
    }
    .suggestions-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .suggestion-chip {
      background: #f5f3ff;
      color: #6d28d9;
      border: 1px solid #ddd6fe;
      border-radius: 8px;
      padding: 6px 12px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .suggestion-chip:hover {
      background: #ede9fe;
      border-color: #c4b5fd;
    }
    .error-banner {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
      padding: 14px 18px;
      border-radius: 14px;
      font-size: 0.9rem;
      margin-bottom: 24px;
    }
    .results-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .executive-card {
      background: linear-gradient(135deg, #3b0764 0%, #1e1b4b 100%);
      color: #ffffff;
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 10px 25px rgba(59, 7, 100, 0.25);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .executive-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 14px;
    }
    .report-type-tag {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #c4b5fd;
      letter-spacing: 0.05em;
    }
    .report-title {
      font-size: 1.4rem;
      font-weight: 900;
      margin: 4px 0 0 0;
    }
    .export-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .btn-export-excel {
      background: #059669;
      color: #ffffff;
      border: none;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    .btn-export-excel:hover {
      background: #047857;
    }
    .btn-export-pdf {
      background: #dc2626;
      color: #ffffff;
      border: none;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    .btn-export-pdf:hover {
      background: #b91c1c;
    }
    .diagnosis-box {
      background: rgba(255,255,255,0.1);
      backdrop-filter: blur(8px);
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 0.9rem;
      line-height: 1.5;
      color: #f5f3ff;
    }
    .kpis-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
    }
    .kpi-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .kpi-label {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #64748b;
    }
    .kpi-val {
      font-size: 1.5rem;
      font-weight: 900;
      color: #0f172a;
    }
    .chart-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .card-section-title {
      margin: 0;
      font-size: 0.95rem;
      font-weight: 800;
      color: #334155;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .bars-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .bar-row {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .bar-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
      font-weight: 600;
    }
    .bar-name { color: #475569; }
    .bar-value { color: #6d28d9; font-weight: 800; }
    .bar-track {
      width: 100%;
      height: 12px;
      background: #f1f5f9;
      border-radius: 9999px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      background: #7c3aed;
      border-radius: 9999px;
      transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .table-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      overflow: hidden;
    }
    .table-header {
      padding: 16px 20px;
      font-weight: 800;
      font-size: 0.9rem;
      color: #334155;
      border-bottom: 1px solid #e2e8f0;
    }
    .table-wrapper {
      overflow-x: auto;
    }
    .report-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      text-align: left;
    }
    .report-table th {
      background: #f8fafc;
      padding: 12px 16px;
      font-weight: 700;
      color: #475569;
      border-bottom: 1px solid #e2e8f0;
    }
    .report-table td {
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
      color: #1e293b;
    }
    .report-table tr:hover td {
      background: #f8fafc;
    }
    @keyframes pulseRecord {
      0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
      50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in { animation: fadeIn 0.2s ease-out; }
  `]
})
export class ReporteIaComponent {
  private controller = inject(CU34ReporteGenerativoIaController);

  prompt = '';
  cargando = false;
  exportando = false;
  escuchandoVoz = false;
  canalUtilizado: 'texto' | 'voz' = 'texto';
  errorMsg = '';
  reporte: ReporteIaResponse | null = null;

  sugerenciasWhitelist = [
    'Mostrame las ventas de septiembre agrupadas por sucursal',
    '¿Cuáles fueron los diez productos más vendidos?',
    'Generá un gráfico de ventas por semana',
    'Rotación y stock crítico por categoría',
    'Métodos de pago y canales de venta',
  ];

  seleccionarSugerencia(s: string): void {
    this.prompt = s;
    this.consultarIa('texto');
  }

  consultarIa(canal: 'texto' | 'voz'): void {
    if (!this.prompt.trim()) return;
    this.cargando = true;
    this.errorMsg = '';
    this.canalUtilizado = canal;

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
      alert('Tu navegador no soporta Web Speech API para dictado por voz. Te sugerimos usar Google Chrome o Microsoft Edge.');
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
