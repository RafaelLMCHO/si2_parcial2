import { Component, ElementRef, OnInit, OnDestroy, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  CU36VestidorVirtualRaController,
  PrendaArResponse,
} from '../../controller/cu36_vestidor_virtual_ra_controller';

@Component({
  selector: 'app-vestidor-virtual',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 max-w-7xl mx-auto space-y-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-gray-200 gap-4">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-bold text-gray-900">CU-36: Vestidor Virtual con Realidad Aumentada (RA)</h1>
            <span class="px-2.5 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
              Cámara Web & Móvil
            </span>
          </div>
          <p class="text-sm text-gray-500">
            Superposición en tiempo real de prendas textiles sobre la silueta corporal o avatar 3D interactivo
          </p>
        </div>
      </div>

      <!-- Selector de Prenda AR y Ajustes de Talla/Color -->
      <div class="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <label class="text-sm font-semibold text-gray-700">Prenda:</label>
          <select
            [(ngModel)]="prendaSeleccionadaId"
            (change)="onPrendaCambiada()"
            class="p-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500">
            <option *ngFor="let p of prendasAr" [value]="p.prenda_id">
              {{ p.nombre_prenda }} ({{ p.categoria }})
            </option>
          </select>
        </div>

        <!-- Selector de Talla -->
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-gray-500 uppercase">Talla:</span>
          <div class="flex gap-1">
            <button
              *ngFor="let t of tallas"
              (click)="tallaSeleccionada = t"
              [class.bg-indigo-600]="tallaSeleccionada === t"
              [class.text-white]="tallaSeleccionada === t"
              [class.bg-gray-100]="tallaSeleccionada !== t"
              class="w-8 h-8 rounded-lg text-xs font-bold transition flex items-center justify-center">
              {{ t }}
            </button>
          </div>
        </div>

        <!-- Selector de Color -->
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-gray-500 uppercase">Color:</span>
          <div class="flex gap-1.5">
            <button
              *ngFor="let c of colores"
              (click)="colorSeleccionado = c"
              [style.backgroundColor]="c.hex"
              [class.ring-2]="colorSeleccionado.hex === c.hex"
              class="w-6 h-6 rounded-full ring-offset-2 ring-indigo-600 border border-gray-300 transition"
              [title]="c.nombre"></button>
          </div>
        </div>

        <!-- Acciones Cámara -->
        <div class="flex items-center gap-2">
          <button
            *ngIf="!camaraActiva"
            (click)="iniciarCamara()"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-xl shadow transition flex items-center gap-1.5">
            📷 Activar Cámara RA
          </button>
          <button
            *ngIf="camaraActiva"
            (click)="detenerCamara()"
            class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white font-medium text-xs rounded-xl shadow transition">
            Detener Cámara
          </button>
          <button
            *ngIf="camaraActiva"
            (click)="capturarFoto()"
            class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs rounded-xl shadow transition flex items-center gap-1.5">
            📸 Capturar Ajuste
          </button>
        </div>
      </div>

      <!-- Área de Visualización RA / Fallback Maniquí 2D -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Contenedor Principal de la Cámara / AR Canvas (2 columnas) -->
        <div class="lg:col-span-2 bg-black rounded-3xl overflow-hidden relative min-h-[500px] flex items-center justify-center shadow-2xl border-4 border-gray-900">
          <!-- Video de la cámara -->
          <video
            #videoElement
            autoplay
            playsinline
            muted
            [class.hidden]="!camaraActiva"
            class="w-full h-full object-cover"></video>

          <!-- Canvas para superposición de Prenda AR y Tracking -->
          <canvas
            #arCanvas
            [class.hidden]="!camaraActiva"
            class="absolute inset-0 w-full h-full pointer-events-none"></canvas>

          <!-- Fallback cuando la cámara no está activa -->
          <div *ngIf="!camaraActiva" class="flex flex-col items-center justify-center text-center p-8 space-y-4">
            <div class="w-32 h-44 border-2 border-dashed border-gray-600 rounded-3xl flex items-center justify-center text-5xl relative bg-gray-900/50">
              <span [style.color]="colorSeleccionado.hex">👕</span>
              <!-- Indicador de talla sobre el maniquí -->
              <span class="absolute bottom-2 px-2 py-0.5 bg-indigo-600 text-[10px] text-white font-bold rounded">
                {{ tallaSeleccionada }}
              </span>
            </div>
            <div class="space-y-1">
              <h3 class="text-white font-bold text-lg">Modo Probador Silueta (Maniquí 2D)</h3>
              <p class="text-xs text-gray-400 max-w-sm">
                Pulsa "Activar Cámara RA" para probarte la prenda en tiempo real sobre tu cuerpo, o ajusta color y talla en el simulador.
              </p>
            </div>
            <button
              (click)="iniciarCamara()"
              class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl transition shadow-lg">
              Conceder Permiso y Activar Cámara
            </button>
          </div>

          <!-- Overlay HUD RA con información de anclaje -->
          <div *ngIf="camaraActiva" class="absolute top-4 left-4 bg-black/60 backdrop-blur-md px-3 py-2 rounded-xl text-white text-xs space-y-0.5">
            <div class="font-bold flex items-center gap-1.5 text-emerald-400">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Tracking Corporal Activo
            </div>
            <div class="text-[11px] text-gray-300">
              Talla: {{ tallaSeleccionada }} | Color: {{ colorSeleccionado.nombre }}
            </div>
          </div>
        </div>

        <!-- Panel Lateral de Ajuste y Detalles de la Prenda -->
        <div class="bg-white rounded-3xl border border-gray-200 p-6 shadow-sm space-y-5">
          <div class="border-b border-gray-100 pb-4">
            <span class="text-xs font-semibold uppercase text-indigo-600 tracking-wider">Detalles de la Prenda</span>
            <h2 class="text-lg font-bold text-gray-900 mt-1">
              {{ prendaActual?.nombre_prenda || 'Prenda en Vestidor' }}
            </h2>
            <span class="text-xs text-gray-500 font-mono">{{ prendaActual?.codigo_prenda }}</span>
          </div>

          <!-- Proporciones y Medidas Anatómicas -->
          <div class="space-y-3">
            <h3 class="text-xs font-bold text-gray-700 uppercase">Puntos Anatómicos de Ajuste (AR)</h3>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="p-2.5 bg-gray-50 rounded-xl">
                <span class="text-gray-400 block text-[10px]">Hombros</span>
                <span class="font-bold text-gray-800">±25 cm (Tracking OK)</span>
              </div>
              <div class="p-2.5 bg-gray-50 rounded-xl">
                <span class="text-gray-400 block text-[10px]">Cuello</span>
                <span class="font-bold text-gray-800">Anclaje Frontal</span>
              </div>
              <div class="p-2.5 bg-gray-50 rounded-xl">
                <span class="text-gray-400 block text-[10px]">Largo Torso</span>
                <span class="font-bold text-gray-800">{{ obtenerEscalaTalla() }}x Escala</span>
              </div>
              <div class="p-2.5 bg-gray-50 rounded-xl">
                <span class="text-gray-400 block text-[10px]">Modelo 3D</span>
                <span class="font-bold text-indigo-600">GLB Adaptativo</span>
              </div>
            </div>
          </div>

          <!-- Foto Capturada -->
          <div *ngIf="fotoCapturada" class="space-y-2 pt-2 border-t border-gray-100">
            <span class="text-xs font-bold text-emerald-700 uppercase">Captura de Prueba Guardada</span>
            <div class="rounded-xl overflow-hidden border border-gray-200">
              <img [src]="fotoCapturada" alt="Captura AR" class="w-full h-40 object-cover" />
            </div>
          </div>
        </div>
      </div>
    </div>
  `
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

  tallas = ['S', 'M', 'L', 'XL'];
  tallaSeleccionada = 'M';

  colores = [
    { nombre: 'Azul Marino', hex: '#1E3A8A' },
    { nombre: 'Negro Clásico', hex: '#111827' },
    { nombre: 'Carmesí', hex: '#DC2626' },
    { nombre: 'Verde Olivo', hex: '#15803D' },
  ];
  colorSeleccionado = this.colores[0];

  ngOnInit(): void {
    this.cargarCatalogoAr();
  }

  ngOnDestroy(): void {
    this.detenerCamara();
  }

  cargarCatalogoAr(): void {
    this.controller.listarPrendasAr().subscribe({
      next: (prendas) => {
        this.prendasAr = prendas;
        if (prendas.length > 0) {
          this.prendaSeleccionadaId = prendas[0].prenda_id;
          this.prendaActual = prendas[0];
        }
      },
    });
  }

  onPrendaCambiada(): void {
    this.prendaActual = this.prendasAr.find((p) => p.prenda_id === this.prendaSeleccionadaId) || null;
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
    } catch (err) {
      alert('No se pudo acceder a la cámara frontal del dispositivo. Asegúrate de conceder permisos.');
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

        // Simulación de tracking anatómico sobre el torso
        const centroX = canvas.width / 2;
        const hombroY = canvas.height * 0.35;
        const escala = this.obtenerEscalaTalla();
        const anchoPrenda = canvas.width * 0.42 * escala;
        const altoPrenda = canvas.height * 0.48 * escala;

        // Renderizado de la prenda adaptativa con el color seleccionado
        ctx.save();
        ctx.fillStyle = this.colorSeleccionado.hex;
        ctx.globalAlpha = 0.85;

        // Silueta poligonal de camiseta sobre el torso
        ctx.beginPath();
        // Cuello
        ctx.moveTo(centroX - anchoPrenda * 0.2, hombroY);
        ctx.quadraticCurveTo(centroX, hombroY + 30, centroX + anchoPrenda * 0.2, hombroY);
        // Hombro derecho y manga
        ctx.lineTo(centroX + anchoPrenda * 0.5, hombroY + 20);
        ctx.lineTo(centroX + anchoPrenda * 0.65, hombroY + 110);
        ctx.lineTo(centroX + anchoPrenda * 0.45, hombroY + 130);
        ctx.lineTo(centroX + anchoPrenda * 0.38, hombroY + 90);
        // Costado derecho
        ctx.lineTo(centroX + anchoPrenda * 0.35, hombroY + altoPrenda);
        // Base inferior
        ctx.lineTo(centroX - anchoPrenda * 0.35, hombroY + altoPrenda);
        // Costado izquierdo
        ctx.lineTo(centroX - anchoPrenda * 0.38, hombroY + 90);
        ctx.lineTo(centroX - anchoPrenda * 0.45, hombroY + 130);
        ctx.lineTo(centroX - anchoPrenda * 0.65, hombroY + 110);
        ctx.lineTo(centroX - anchoPrenda * 0.5, hombroY + 20);
        ctx.closePath();
        ctx.fill();

        // Contorno sutil
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Texto de Talla y Marca
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 16px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${this.tallaSeleccionada}`, centroX, hombroY + altoPrenda * 0.4);

        ctx.restore();
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

    ctx.drawImage(video, 0, 0);
    ctx.drawImage(ar, 0, 0);

    this.fotoCapturada = canvas.toDataURL('image/jpeg');
  }
}

