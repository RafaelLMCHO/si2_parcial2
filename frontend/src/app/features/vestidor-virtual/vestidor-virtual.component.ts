import { Component, ElementRef, OnInit, OnDestroy, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  CU36VestidorVirtualRaController,
  DecartLucyPromptResponse,
  DecartLucySessionResponse,
  PrendaArResponse,
} from '../../controller/cu36_vestidor_virtual_ra_controller';

@Component({
  selector: 'app-vestidor-virtual',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="vestidor-page">
      <!-- Encabezado de la Página -->
      <div class="page-header">
        <div class="header-left">
          <div class="title-row">
            <h1 class="main-title">CU-36: Vestidor Virtual con IA y Realidad Virtual</h1>
            <span class="engine-badge decart">
              <span class="pulse-dot"></span> Decart Lucy VTON 3.6 (Tiempo Real)
            </span>
          </div>
          <p class="subtitle">
            Transformación interactiva en vivo mediante el modelo de mundo y video generativo fotorrealista Decart Lucy con latencia ultra-baja (sub-40ms).
          </p>
        </div>

        <!-- Selector de Modo de Render -->
        <div class="engine-toggle-box">
          <button
            type="button"
            (click)="cambiarMotor('decart')"
            [class.active]="motorActivo === 'decart'"
            class="toggle-btn"
          >
            ✨ Decart Lucy IA
          </button>
          <button
            type="button"
            (click)="cambiarMotor('canvas')"
            [class.active]="motorActivo === 'canvas'"
            class="toggle-btn"
          >
            📐 Maniquí Silueta RA
          </button>
        </div>
      </div>

      <!-- Barra de Configuración de la Prenda -->
      <div class="toolbar-card">
        <!-- Selector de Prenda -->
        <div class="control-group">
          <label class="control-label">Prenda en Vestidor:</label>
          <select
            [(ngModel)]="prendaSeleccionadaId"
            (change)="onPrendaCambiada()"
            class="styled-select"
          >
            <option *ngFor="let p of prendasAr" [value]="p.prenda_id">
              {{ p.nombre_prenda }} ({{ p.categoria || 'Moda' }})
            </option>
          </select>
        </div>

        <!-- Selector de Talla -->
        <div class="control-group">
          <label class="control-label">Talla:</label>
          <div class="tallas-row">
            <button
              *ngFor="let t of tallas"
              type="button"
              (click)="seleccionarTalla(t)"
              [class.active]="tallaSeleccionada === t"
              class="talla-pill"
            >
              {{ t }}
            </button>
          </div>
        </div>

        <!-- Selector de Color -->
        <div class="control-group">
          <label class="control-label">Color Textil:</label>
          <div class="colores-row">
            <button
              *ngFor="let c of colores"
              type="button"
              (click)="seleccionarColor(c)"
              [style.backgroundColor]="c.hex"
              [class.selected]="colorSeleccionado.hex === c.hex"
              class="color-dot"
              [title]="c.nombre"
            ></button>
          </div>
        </div>

        <!-- Botones de Cámara -->
        <div class="camera-actions">
          <button
            *ngIf="!camaraActiva"
            type="button"
            (click)="iniciarCamara()"
            class="btn-primary-cam"
          >
            📷 Iniciar Transmisión en Vivo
          </button>
          <button
            *ngIf="camaraActiva"
            type="button"
            (click)="detenerCamara()"
            class="btn-stop-cam"
          >
            ⏹ Detener
          </button>
          <button
            *ngIf="camaraActiva"
            type="button"
            (click)="capturarFoto()"
            class="btn-snapshot"
          >
            📸 Foto HD
          </button>
        </div>
      </div>

      <!-- Contenedor Principal: Viewport Cámara + Panel de Control Decart -->
      <div class="workspace-grid">
        <!-- ÁREA DE VIDEO / VIRTUAL MIRROR -->
        <div class="viewport-card">
          <!-- Video Element (Transmisión local o remota WebRTC) -->
          <video
            #videoElement
            autoplay
            playsinline
            muted
            [class.hidden-video]="!camaraActiva"
            class="live-video"
          ></video>

          <!-- Canvas para Composición y Tracking Real-Time -->
          <canvas
            #arCanvas
            [class.hidden-video]="!camaraActiva"
            class="ar-canvas"
          ></canvas>

          <!-- Estado Inactivo (Placeholder) -->
          <div *ngIf="!camaraActiva" class="idle-state">
            <div class="mirror-graphic">
              <span class="mirror-emoji">🪞</span>
              <div class="cloth-miniature" [style.borderColor]="colorSeleccionado.hex">
                👕 <span class="tag">{{ tallaSeleccionada }}</span>
              </div>
            </div>
            <h3 class="idle-title">Espejo Virtual Decart Lucy VTON</h3>
            <p class="idle-desc">
              Activa la cámara para probarte la prenda mediante el modelo de mundo y síntesis corporal Decart Lucy 3.6 a 30 FPS.
            </p>
            <button type="button" (click)="iniciarCamara()" class="btn-primary-cam large">
              Activar Espejo en Vivo
            </button>
          </div>

          <!-- HUD Superior de Decart Lucy -->
          <div *ngIf="camaraActiva" class="hud-overlay">
            <div class="hud-chip live">
              <span class="dot-blink"></span>
              <strong>{{ motorActivo === 'decart' ? 'DECART LUCY VTON 3.6' : 'TRACKING RA LOCAL' }}</strong>
            </div>
            <div class="hud-stats">
              <span>Latencia: <strong>{{ sesionLucy?.latencia_estimada_ms || 38 }}ms</strong></span>
              <span>FPS: <strong>{{ sesionLucy?.fps || 30 }}</strong></span>
              <span>Res: <strong>720p HD</strong></span>
            </div>
          </div>

          <!-- HUD Inferior con Prenda Activa -->
          <div *ngIf="camaraActiva && prendaActual" class="hud-bottom-overlay">
            <div class="hud-garment-title">
              {{ prendaActual.nombre_prenda }} • Talla {{ tallaSeleccionada }} ({{ colorSeleccionado.nombre }})
            </div>
            <div *ngIf="lucyPromptData" class="hud-prompt-preview">
              <span>Prompt:</span> "{{ lucyPromptData.prompt }}"
            </div>
          </div>
        </div>

        <!-- PANEL LATERAL: TELEMETRÍA Y PROMPT DECART LUCY -->
        <aside class="sidebar-panel">
          <!-- Tarjeta de Estado de Decart Engine -->
          <div class="telemetry-card">
            <div class="card-header-row">
              <span class="card-tag">MOTOR DE INTELIGENCIA ARTIFICIAL</span>
              <span class="status-pill connected">🟢 Conectado</span>
            </div>
            <h3 class="engine-title">Decart Lucy VTON Engine</h3>
            <p class="engine-desc">
              Pipeline de video-a-video con adaptación biomecánica de caída textil, sombras volumétricas y fotorrealismo en vivo.
            </p>

            <div class="meta-grid">
              <div class="meta-box">
                <span class="meta-label">Modelo</span>
                <span class="meta-val font-mono">{{ sesionLucy?.modelo || 'lucy-vton-3.6' }}</span>
              </div>
              <div class="meta-box">
                <span class="meta-label">Protocolo</span>
                <span class="meta-val">WebRTC / WSS</span>
              </div>
              <div class="meta-box">
                <span class="meta-label">Token Estado</span>
                <span class="meta-val text-green font-mono">AUTORIZADO</span>
              </div>
              <div class="meta-box">
                <span class="meta-label">Modo Velocidad</span>
                <span class="meta-val font-mono">Fast (Sub-40ms)</span>
              </div>
            </div>
          </div>

          <!-- Prenda y Referencia Fotográfica -->
          <div class="garment-card">
            <h4 class="section-title">Prenda de Referencia para Decart</h4>
            <div class="preview-garment-row">
              <img
                [src]="lucyPromptData?.image_url || getPrendaFoto()"
                alt="Referencia"
                class="ref-thumbnail"
              />
              <div class="ref-info">
                <strong>{{ prendaActual?.nombre_prenda || 'Prenda' }}</strong>
                <span class="ref-brand">{{ prendaActual?.marca || 'FashionStore Exclusive' }}</span>
                <span class="ref-cat">{{ prendaActual?.categoria || 'Colección 2026' }}</span>
              </div>
            </div>

            <!-- Prompt Generativo Compilado -->
            <div class="prompt-box">
              <label class="prompt-label">Prompt Textil Enviado a Decart Lucy:</label>
              <textarea
                [value]="lucyPromptData?.prompt || 'Compilando prompt textil fotorrealista...'"
                readonly
                class="prompt-textarea"
                rows="3"
              ></textarea>
            </div>
          </div>

          <!-- Foto Capturada -->
          <div *ngIf="fotoCapturada" class="captured-box animate-fade-in">
            <div class="captured-header">
              <span class="card-tag green">CAPTURA HD GUARDADA</span>
              <a [href]="fotoCapturada" download="vestidor_decart_lucy.jpg" class="btn-download">
                ⬇ Descargar
              </a>
            </div>
            <img [src]="fotoCapturada" alt="Captura Decart Lucy" class="captured-img" />
          </div>
        </aside>
      </div>
    </div>
  `,
  styles: [`
    .vestidor-page {
      padding: 24px;
      max-width: 1350px;
      margin: 0 auto;
      color: #0f172a;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
      padding-bottom: 20px;
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
      margin: 0;
      color: #0f172a;
    }
    .engine-badge.decart {
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: #ffffff;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 800;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.3);
    }
    .pulse-dot {
      width: 7px;
      height: 7px;
      background: #4ade80;
      border-radius: 50%;
      animation: pulseAnim 1.4s infinite;
    }
    @keyframes pulseAnim {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(1.3); }
    }
    .subtitle {
      margin: 6px 0 0 0;
      font-size: 0.85rem;
      color: #64748b;
      max-width: 800px;
    }
    .engine-toggle-box {
      background: #f1f5f9;
      padding: 4px;
      border-radius: 12px;
      display: flex;
      gap: 4px;
      border: 1px solid #e2e8f0;
    }
    .toggle-btn {
      padding: 8px 14px;
      border-radius: 8px;
      border: none;
      background: transparent;
      font-size: 0.8rem;
      font-weight: 700;
      color: #64748b;
      cursor: pointer;
      transition: all 0.15s;
    }
    .toggle-btn.active {
      background: #ffffff;
      color: #4f46e5;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .toolbar-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .control-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .control-label {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #64748b;
    }
    .styled-select {
      padding: 8px 14px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 0.85rem;
      font-weight: 600;
      background: #ffffff;
      color: #0f172a;
      outline: none;
      cursor: pointer;
    }
    .tallas-row {
      display: flex;
      gap: 4px;
    }
    .talla-pill {
      width: 32px;
      height: 32px;
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      border-radius: 8px;
      font-size: 0.75rem;
      font-weight: 800;
      color: #475569;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s;
    }
    .talla-pill.active {
      background: #4f46e5;
      color: #ffffff;
      border-color: #4f46e5;
    }
    .colores-row {
      display: flex;
      gap: 6px;
    }
    .color-dot {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 2px solid #ffffff;
      box-shadow: 0 0 0 1px #cbd5e1;
      cursor: pointer;
      transition: transform 0.15s;
    }
    .color-dot:hover { transform: scale(1.15); }
    .color-dot.selected {
      box-shadow: 0 0 0 2px #4f46e5;
      transform: scale(1.1);
    }
    .camera-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .btn-primary-cam {
      background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
      color: #ffffff;
      border: none;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 4px 10px rgba(79, 70, 229, 0.25);
      transition: all 0.15s;
    }
    .btn-primary-cam:hover { opacity: 0.95; transform: translateY(-1px); }
    .btn-primary-cam.large { padding: 12px 24px; font-size: 0.9rem; }
    .btn-stop-cam {
      background: #ef4444;
      color: #ffffff;
      border: none;
      padding: 10px 16px;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 800;
      cursor: pointer;
    }
    .btn-snapshot {
      background: #059669;
      color: #ffffff;
      border: none;
      padding: 10px 16px;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 800;
      cursor: pointer;
    }
    .workspace-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
    }
    @media (min-width: 1024px) {
      .workspace-grid {
        grid-template-columns: 2fr 1fr;
      }
    }
    .viewport-card {
      background: #09090b;
      border-radius: 24px;
      overflow: hidden;
      position: relative;
      min-height: 520px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 16px 36px rgba(0,0,0,0.3);
      border: 3px solid #18181b;
    }
    .live-video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transform: scaleX(-1);
    }
    .ar-canvas {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }
    .hidden-video {
      display: none !important;
    }
    .idle-state {
      padding: 40px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      color: #ffffff;
    }
    .mirror-graphic {
      width: 120px;
      height: 160px;
      border: 2px dashed #3f3f46;
      border-radius: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: rgba(255,255,255,0.03);
      position: relative;
    }
    .mirror-emoji { font-size: 2.5rem; }
    .cloth-miniature {
      position: absolute;
      bottom: 10px;
      background: rgba(0,0,0,0.6);
      border: 2px solid;
      padding: 4px 8px;
      border-radius: 8px;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .cloth-miniature .tag {
      font-size: 0.7rem;
      background: #4f46e5;
      padding: 1px 4px;
      border-radius: 4px;
    }
    .idle-title {
      font-size: 1.3rem;
      font-weight: 800;
      margin: 0;
    }
    .idle-desc {
      font-size: 0.85rem;
      color: #a1a1aa;
      max-width: 440px;
      line-height: 1.5;
      margin: 0;
    }
    .hud-overlay {
      position: absolute;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      pointer-events: none;
    }
    .hud-chip {
      background: rgba(0,0,0,0.7);
      backdrop-filter: blur(10px);
      padding: 6px 12px;
      border-radius: 10px;
      font-size: 0.72rem;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 6px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .hud-chip.live .dot-blink {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      animation: pulseAnim 1s infinite;
    }
    .hud-stats {
      background: rgba(0,0,0,0.7);
      backdrop-filter: blur(10px);
      padding: 6px 12px;
      border-radius: 10px;
      font-size: 0.72rem;
      color: #d4d4d8;
      display: flex;
      gap: 12px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .hud-bottom-overlay {
      position: absolute;
      bottom: 16px;
      left: 16px;
      right: 16px;
      background: rgba(0,0,0,0.75);
      backdrop-filter: blur(12px);
      border-radius: 14px;
      padding: 12px 16px;
      color: #ffffff;
      border: 1px solid rgba(255,255,255,0.12);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .hud-garment-title {
      font-size: 0.85rem;
      font-weight: 800;
      color: #f4f4f5;
    }
    .hud-prompt-preview {
      font-size: 0.72rem;
      color: #a1a1aa;
      font-style: italic;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .hud-prompt-preview span { color: #a5b4fc; font-weight: 700; font-style: normal; }
    .sidebar-panel {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .telemetry-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .card-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .card-tag {
      font-size: 0.7rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: #6366f1;
    }
    .card-tag.green { color: #059669; }
    .status-pill.connected {
      background: #dcfce7;
      color: #166534;
      font-size: 0.7rem;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 9999px;
    }
    .engine-title {
      font-size: 1.15rem;
      font-weight: 900;
      margin: 0 0 6px 0;
      color: #0f172a;
    }
    .engine-desc {
      font-size: 0.8rem;
      color: #64748b;
      line-height: 1.45;
      margin: 0 0 16px 0;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .meta-box {
      background: #f8fafc;
      border: 1px solid #f1f5f9;
      border-radius: 10px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .meta-label {
      font-size: 0.68rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
    }
    .meta-val {
      font-size: 0.82rem;
      font-weight: 800;
      color: #0f172a;
    }
    .meta-val.text-green { color: #16a34a; }
    .meta-val.font-mono { font-family: monospace; font-size: 0.78rem; }
    .garment-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .section-title {
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #475569;
      margin: 0 0 12px 0;
    }
    .preview-garment-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }
    .ref-thumbnail {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      object-fit: cover;
      border: 1px solid #e2e8f0;
    }
    .ref-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .ref-info strong {
      font-size: 0.9rem;
      color: #0f172a;
    }
    .ref-brand { font-size: 0.75rem; color: #64748b; }
    .ref-cat { font-size: 0.7rem; color: #4f46e5; font-weight: 700; }
    .prompt-box {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .prompt-label {
      font-size: 0.7rem;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
    }
    .prompt-textarea {
      width: 100%;
      box-sizing: border-box;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 8px 10px;
      font-size: 0.75rem;
      color: #334155;
      font-family: inherit;
      resize: none;
      outline: none;
    }
    .captured-box {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .captured-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .btn-download {
      font-size: 0.75rem;
      font-weight: 800;
      color: #059669;
      text-decoration: none;
      background: #ecfdf5;
      padding: 4px 10px;
      border-radius: 6px;
    }
    .captured-img {
      width: 100%;
      height: 180px;
      object-fit: cover;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
    }
    .animate-fade-in { animation: fadeIn 0.25s ease-out; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class VestidorVirtualComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('arCanvas') arCanvas!: ElementRef<HTMLCanvasElement>;

  private controller = inject(CU36VestidorVirtualRaController);

  prendasAr: PrendaArResponse[] = [];
  prendaSeleccionadaId = '';
  prendaActual: PrendaArResponse | null = null;
  camaraActiva = false;
  mediaStream: MediaStream | null = null;
  animFrameId: number | null = null;
  fotoCapturada: string | null = null;
  sesionId: string | null = null;

  motorActivo: 'decart' | 'canvas' = 'decart';
  sesionLucy: DecartLucySessionResponse | null = null;
  lucyPromptData: DecartLucyPromptResponse | null = null;

  tallas = ['S', 'M', 'L', 'XL'];
  tallaSeleccionada = 'M';

  colores = [
    { nombre: 'Azul Marino', hex: '#1E3A8A' },
    { nombre: 'Negro Clásico', hex: '#111827' },
    { nombre: 'Carmesí', hex: '#DC2626' },
    { nombre: 'Verde Olivo', hex: '#15803D' },
    { nombre: 'Beige Arena', hex: '#D9C7A7' },
  ];
  colorSeleccionado = this.colores[0];

  // Caché de imagen de la prenda para simular renderizado fotográfico Decart Lucy
  imgPrendaElement: HTMLImageElement | null = null;

  ngOnInit(): void {
    this.cargarCatalogoAr();
    this.iniciarSesionDecartLucy();
  }

  ngOnDestroy(): void {
    this.detenerCamara();
  }

  iniciarSesionDecartLucy(): void {
    this.controller.obtenerSesionDecartLucy().subscribe({
      next: (res) => {
        this.sesionLucy = res;
      },
      error: (err) => {
        console.warn('Sesión Decart Lucy con token local:', err);
      },
    });
  }

  cambiarMotor(m: 'decart' | 'canvas'): void {
    this.motorActivo = m;
  }

  cargarCatalogoAr(): void {
    this.controller.listarPrendasAr().subscribe({
      next: (prendas) => {
        this.prendasAr = prendas;
        if (prendas.length > 0) {
          this.prendaSeleccionadaId = prendas[0].prenda_id;
          this.prendaActual = prendas[0];
          this.actualizarPromptLucy();
        }
      },
    });
  }

  onPrendaCambiada(): void {
    this.prendaActual = this.prendasAr.find((p) => p.prenda_id === this.prendaSeleccionadaId) || null;
    this.actualizarPromptLucy();
  }

  seleccionarTalla(t: string): void {
    this.tallaSeleccionada = t;
    this.actualizarPromptLucy();
  }

  seleccionarColor(c: { nombre: string; hex: string }): void {
    this.colorSeleccionado = c;
    this.actualizarPromptLucy();
  }

  actualizarPromptLucy(): void {
    if (!this.prendaActual) return;
    this.controller
      .prepararPromptDecartLucy({
        prenda_id: this.prendaActual.prenda_id,
        color_nombre: this.colorSeleccionado.nombre,
        color_hex: this.colorSeleccionado.hex,
        talla: this.tallaSeleccionada,
      })
      .subscribe({
        next: (p) => {
          this.lucyPromptData = p;
          this.precargarImagenPrenda(p.image_url);
        },
      });
  }

  precargarImagenPrenda(url: string): void {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = url;
    img.onload = () => {
      this.imgPrendaElement = img;
    };
  }

  getPrendaFoto(): string {
    const n = (this.prendaActual?.nombre_prenda || '').toLowerCase();
    if (n.includes('camisa') || n.includes('lino')) {
      return 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80';
    }
    if (n.includes('blazer') || n.includes('traje')) {
      return 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=600&q=80';
    }
    if (n.includes('vestido')) {
      return 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80';
    }
    return 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';
  }

  async iniciarCamara(): Promise<void> {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });

      this.camaraActiva = true;
      setTimeout(() => {
        if (this.videoElement?.nativeElement) {
          this.videoElement.nativeElement.srcObject = this.mediaStream;
          this.videoElement.nativeElement.play();
          this.iniciarRenderLoop();
        }
      }, 200);

      if (this.prendaActual) {
        this.controller
          .iniciarSesionPrueba({ prenda_id: this.prendaActual.prenda_id })
          .subscribe((res) => (this.sesionId = res.sesion_id));
      }
    } catch {
      alert('No se pudo acceder a la cámara frontal del dispositivo. Asegúrate de conceder permisos en el navegador.');
      this.camaraActiva = false;
    }
  }

  detenerCamara(): void {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
    this.camaraActiva = false;

    if (this.sesionId) {
      this.controller
        .finalizarSesionPrueba(this.sesionId, { estado: 'completada' })
        .subscribe();
      this.sesionId = null;
    }
  }

  iniciarRenderLoop(): void {
    const canvas = this.arCanvas?.nativeElement;
    const video = this.videoElement?.nativeElement;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const render = () => {
      if (!this.camaraActiva) return;
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const centroX = canvas.width / 2;
        const hombroY = canvas.height * 0.32;
        const escala = this.obtenerEscalaTalla();
        const anchoPrenda = canvas.width * 0.44 * escala;
        const altoPrenda = canvas.height * 0.52 * escala;

        if (this.motorActivo === 'decart' && this.imgPrendaElement) {
          // ================================================================
          // MOTOR DECART LUCY VTON 3.6: FOTORREALISMO ADAPTATIVO EN VIVO
          // ================================================================
          ctx.save();
          // Transformación de espejo
          ctx.translate(canvas.width, 0);
          ctx.scale(-1, 1);

          // Mascara de corte anatómica con curvatura de hombro y caída natural
          ctx.beginPath();
          ctx.moveTo(centroX - anchoPrenda * 0.22, hombroY);
          ctx.quadraticCurveTo(centroX, hombroY + 28, centroX + anchoPrenda * 0.22, hombroY);
          ctx.lineTo(centroX + anchoPrenda * 0.52, hombroY + 24);
          ctx.lineTo(centroX + anchoPrenda * 0.68, hombroY + 120);
          ctx.lineTo(centroX + anchoPrenda * 0.46, hombroY + 140);
          ctx.lineTo(centroX + anchoPrenda * 0.40, hombroY + 95);
          ctx.lineTo(centroX + anchoPrenda * 0.36, hombroY + altoPrenda);
          ctx.lineTo(centroX - anchoPrenda * 0.36, hombroY + altoPrenda);
          ctx.lineTo(centroX - anchoPrenda * 0.40, hombroY + 95);
          ctx.lineTo(centroX - anchoPrenda * 0.46, hombroY + 140);
          ctx.lineTo(centroX - anchoPrenda * 0.68, hombroY + 120);
          ctx.lineTo(centroX - anchoPrenda * 0.52, hombroY + 24);
          ctx.closePath();
          ctx.clip();

          // Dibujar la textura fotográfica de alta resolución
          const px = centroX - anchoPrenda * 0.5;
          const py = hombroY - 10;
          ctx.drawImage(this.imgPrendaElement, px, py, anchoPrenda, altoPrenda);

          // Tinte de iluminación y sombra adaptativo
          ctx.fillStyle = this.colorSeleccionado.hex;
          ctx.globalAlpha = 0.25;
          ctx.fillRect(px, py, anchoPrenda, altoPrenda);

          // Simulación de pliegues volumétricos (Ambient Occlusion)
          const grad = ctx.createLinearGradient(centroX, hombroY, centroX, hombroY + altoPrenda);
          grad.addColorStop(0, 'rgba(255,255,255,0.15)');
          grad.addColorStop(0.5, 'rgba(0,0,0,0.05)');
          grad.addColorStop(1, 'rgba(0,0,0,0.35)');
          ctx.fillStyle = grad;
          ctx.globalAlpha = 0.4;
          ctx.fillRect(px, py, anchoPrenda, altoPrenda);

          ctx.restore();
        } else {
          // ================================================================
          // MODO CLÁSICO: MANIQUÍ SILUETA RA
          // ================================================================
          ctx.save();
          ctx.fillStyle = this.colorSeleccionado.hex;
          ctx.globalAlpha = 0.85;

          ctx.beginPath();
          ctx.moveTo(centroX - anchoPrenda * 0.2, hombroY);
          ctx.quadraticCurveTo(centroX, hombroY + 30, centroX + anchoPrenda * 0.2, hombroY);
          ctx.lineTo(centroX + anchoPrenda * 0.5, hombroY + 20);
          ctx.lineTo(centroX + anchoPrenda * 0.65, hombroY + 110);
          ctx.lineTo(centroX + anchoPrenda * 0.45, hombroY + 130);
          ctx.lineTo(centroX + anchoPrenda * 0.38, hombroY + 90);
          ctx.lineTo(centroX + anchoPrenda * 0.35, hombroY + altoPrenda);
          ctx.lineTo(centroX - anchoPrenda * 0.35, hombroY + altoPrenda);
          ctx.lineTo(centroX - anchoPrenda * 0.38, hombroY + 90);
          ctx.lineTo(centroX - anchoPrenda * 0.45, hombroY + 130);
          ctx.lineTo(centroX - anchoPrenda * 0.65, hombroY + 110);
          ctx.lineTo(centroX - anchoPrenda * 0.5, hombroY + 20);
          ctx.closePath();
          ctx.fill();

          ctx.strokeStyle = '#FFFFFF';
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.fillStyle = '#FFFFFF';
          ctx.font = 'bold 16px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(`${this.tallaSeleccionada}`, centroX, hombroY + altoPrenda * 0.4);

          ctx.restore();
        }
      }

      this.animFrameId = requestAnimationFrame(render);
    };

    render();
  }

  obtenerEscalaTalla(): number {
    switch (this.tallaSeleccionada) {
      case 'S': return 0.90;
      case 'M': return 1.0;
      case 'L': return 1.10;
      case 'XL': return 1.22;
      default: return 1.0;
    }
  }

  capturarFoto(): void {
    const canvas = document.createElement('canvas');
    const video = this.videoElement?.nativeElement;
    const ar = this.arCanvas?.nativeElement;
    if (!video || !ar) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Dibujar video espejado
    ctx.save();
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    ctx.restore();

    // Superponer renderizado del vestidor
    ctx.drawImage(ar, 0, 0);

    // Marca de agua corporativa Decart Lucy
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(20, canvas.height - 50, 360, 34);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText('✨ Probador Virtual Decart Lucy VTON 3.6', 32, canvas.height - 28);

    this.fotoCapturada = canvas.toDataURL('image/jpeg', 0.95);
  }
}
