import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';
import { CU26RegistrarReservaOfflineController } from '../../../controller/cu26_registrar_reserva_offline_controller';
import { CU27BloquearStockSoftLockController } from '../../../controller/cu27_bloquear_stock_soft_lock_controller';
import { CatalogoService } from '../../../core/catalogo.service';
import { InventarioService } from '../../../core/inventario.service';
import { DisponibilidadSucursal, Prenda, Variante } from '../../../core/models';

@Component({
  selector: 'app-reserva-offline',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-2xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/offline/reserva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-26: Reserva Offline</a>
        <a routerLink="/offline/bloqueos" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">
          CU-27: Bloqueos Activos ({{ softLockCtrl.bloqueos().length }})
        </a>
        <a routerLink="/offline/cola" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-30/31: Cola y Sync</a>
      </div>

      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-26: Registrar Reserva Offline (UUID Local)</h1>
        <p class="text-sm text-gray-500">Genera una reserva persistida en la cola local y opcionalmente aplica soft-lock temporal (CU-27)</p>
      </div>

      <div class="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 text-xs text-amber-800">
        ⚠️ Modo Desconectado: La reserva se almacenará en la cola Outbox con identificador UUID v4 único y se sincronizará al volver la conexión.
      </div>

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div class="flex justify-end">
          <button
            type="button"
            (click)="modoManual.set(!modoManual())"
            class="text-xs font-semibold text-indigo-600 hover:underline"
          >
            {{ modoManual() ? 'Usar catálogo cacheado' : 'Ingresar UUID manualmente' }}
          </button>
        </div>

        @if (!modoManual() && prendas().length > 0) {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Prenda en Caché</label>
            <select
              [ngModel]="prendaSeleccionadaId()"
              (ngModelChange)="onPrendaChange($event)"
              class="w-full text-sm px-3 py-2 border rounded-lg bg-white"
            >
              @for (p of prendas(); track p.id) {
                <option [value]="p.id">{{ p.nombre }} ({{ p.codigo }})</option>
              }
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Variante (Talla / Color)</label>
            <select [(ngModel)]="varianteId" class="w-full text-sm px-3 py-2 border rounded-lg bg-white">
              @for (v of variantesDisponibles(); track v.id) {
                <option [value]="v.id">{{ v.talla_nombre || 'Talla' }} / {{ v.color_nombre || 'Color' }} ({{ v.sku }})</option>
              }
            </select>
          </div>
        } @else {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Variante ID (UUID)</label>
            <input [(ngModel)]="varianteId" placeholder="UUID de la variante" class="w-full text-sm px-3 py-2 border rounded-lg" />
          </div>
        }

        @if (!modoManual() && sucursalesOpciones().length > 0) {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Sucursal</label>
            <select [(ngModel)]="sucursalId" class="w-full text-sm px-3 py-2 border rounded-lg bg-white">
              @for (s of sucursalesOpciones(); track s.id) {
                <option [value]="s.id">{{ s.nombre }}@if (s.ciudad) { ({{ s.ciudad }})} — {{ s.stockLabel }}</option>
              }
            </select>
          </div>
        } @else {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Sucursal ID (UUID)</label>
            <input [(ngModel)]="sucursalId" placeholder="UUID de la sucursal" class="w-full text-sm px-3 py-2 border rounded-lg" />
          </div>
        }

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Cantidad</label>
            <input type="number" min="1" [(ngModel)]="cantidad" class="w-full text-sm px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Fecha y Hora de Visita</label>
            <input type="datetime-local" [(ngModel)]="fechaVisita" class="w-full text-sm px-3 py-2 border rounded-lg" />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input type="checkbox" id="probador" [(ngModel)]="probador" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="probador" class="text-sm font-medium text-gray-700">Apartar cabina de probador</label>
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" id="aplicarSoftLock" [(ngModel)]="aplicarSoftLock" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="aplicarSoftLock" class="text-sm font-medium text-gray-700">Aplicar Soft-Lock temporal de 45 min (CU-27)</label>
        </div>

        <button
          (click)="guardar()"
          [disabled]="!sucursalId || !varianteId"
          class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition disabled:opacity-50"
        >
          Guardar Reserva en Cola Outbox
        </button>

        @if (ctrl.error(); as err) {
          <div class="p-3 bg-red-50 text-red-700 border border-red-200 rounded-xl text-xs font-semibold">
            {{ err }}
          </div>
        }

        @if (ctrl.reservaUuid(); as uuid) {
          <div class="p-3 bg-green-50 text-green-800 border border-green-200 rounded-xl text-xs font-semibold flex flex-wrap justify-between items-center gap-2">
            <span>Reserva registrada localmente ({{ ctrl.codigoLocal() || uuid.slice(0, 8) }}) • UUID: {{ uuid }}</span>
            <div class="flex gap-3">
              <a routerLink="/reservas/mis-reservas" class="underline font-bold">Mis Reservas</a>
              <a routerLink="/offline/bloqueos" class="underline font-bold">Bloqueos ({{ softLockCtrl.bloqueos().length }})</a>
            </div>
          </div>
        }
      </div>
    </div>
  `
})
export class ReservaOfflineComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly catalogoService = inject(CatalogoService);
  private readonly inventarioService = inject(InventarioService);
  private readonly cu25Offline = inject(CU25DescargarCatalogoOfflineController);
  readonly ctrl = inject(CU26RegistrarReservaOfflineController);
  readonly softLockCtrl = inject(CU27BloquearStockSoftLockController);

  prendas = signal<Prenda[]>([]);
  prendaSeleccionadaId = signal<string>('');
  disponibilidad = signal<DisponibilidadSucursal[]>([]);
  sucursalesCacheadas = signal<Array<{ id: string; nombre: string; ciudad?: string }>>([]);
  modoManual = signal(false);

  sucursalId = '';
  varianteId = '';
  cantidad = 1;
  fechaVisita = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 16);
  probador = true;
  aplicarSoftLock = true;

  variantesDisponibles = computed<Variante[]>(() => {
    const pid = this.prendaSeleccionadaId();
    return this.prendas().find((p) => p.id === pid)?.variantes || [];
  });

  sucursalesOpciones = computed(() => {
    const varId = this.varianteId;
    const byId = new Map<string, { id: string; nombre: string; ciudad: string; stockLabel: string }>();

    for (const s of this.disponibilidad()) {
      const vars = s.variantes || [];
      const match = varId ? vars.find((v) => v.variante_id === varId) : null;
      const qty = match
        ? Number(match.stock_disponible || 0)
        : vars.reduce((acc, v) => acc + Number(v.stock_disponible || 0), 0);
      byId.set(s.sucursal_id, {
        id: s.sucursal_id,
        nombre: s.nombre,
        ciudad: s.ciudad || '',
        stockLabel: `${qty} disp. (local)`,
      });
    }

    for (const s of this.sucursalesCacheadas()) {
      if (!byId.has(s.id)) {
        byId.set(s.id, {
          id: s.id,
          nombre: s.nombre,
          ciudad: s.ciudad || '',
          stockLabel: 'caché local',
        });
      }
    }
    return Array.from(byId.values());
  });

  ngOnInit(): void {
    const qp = this.route.snapshot.queryParamMap;
    const qpSucursal = qp.get('sucursal_id') || '';
    const qpVariante = qp.get('variante_id') || '';
    const qpPrenda = qp.get('prenda_id') || '';
    if (qp.get('cantidad')) this.cantidad = Math.max(1, Number(qp.get('cantidad')) || 1);

    this.cu25Offline.asegurarCatalogoOfflineCargado();

    const sucs = this.inventarioService.obtenerSucursalesOffline();
    this.sucursalesCacheadas.set(sucs);
    if (qpSucursal) {
      this.sucursalId = qpSucursal;
    } else if (sucs.length > 0) {
      this.sucursalId = sucs[0].id;
    }

    const locales = this.catalogoService.obtenerPrendasCacheadas();
    this.prendas.set(locales);
    if (locales.length > 0) {
      let prenda = locales.find((p) => p.id === qpPrenda);
      if (!prenda && qpVariante) {
        prenda = locales.find((p) => p.variantes?.some((v) => v.id === qpVariante));
      }
      prenda = prenda || locales[0];
      this.prendaSeleccionadaId.set(prenda.id);
      const vars = prenda.variantes || [];
      this.varianteId = qpVariante || vars[0]?.id || '';
      this.cargarDisponibilidadPrenda(prenda.id);
    } else if (qpVariante) {
      this.varianteId = qpVariante;
    }

    if (this.prendas().length === 0 || this.sucursalesCacheadas().length === 0) {
      this.modoManual.set(true);
    }

    this.softLockCtrl.listarBloqueosActivos().subscribe();
  }

  onPrendaChange(prendaId: string): void {
    this.prendaSeleccionadaId.set(prendaId);
    const vars = this.variantesDisponibles();
    this.varianteId = vars[0]?.id || '';
    this.cargarDisponibilidadPrenda(prendaId);
  }

  private cargarDisponibilidadPrenda(prendaId: string): void {
    this.inventarioService.consultarDisponibilidad(prendaId).subscribe({
      next: (disp) => this.disponibilidad.set(disp.sucursales || []),
      error: () => {},
    });
  }

  guardar() {
    const qty = Math.max(1, Number(this.cantidad) || 1);
    const prenda = this.prendas().find((p) => p.id === this.prendaSeleccionadaId());
    const variante = this.variantesDisponibles().find((v) => v.id === this.varianteId);
    const sucursal = this.sucursalesOpciones().find((s) => s.id === this.sucursalId);

    if (this.aplicarSoftLock && this.sucursalId && this.varianteId) {
      this.softLockCtrl.bloquearStock(this.varianteId, qty, 45, this.sucursalId);
    }

    this.ctrl.registrarReserva({
      sucursal_id: this.sucursalId,
      sucursal_nombre: sucursal?.nombre || null,
      fecha_visita: new Date(this.fechaVisita).toISOString(),
      probador: this.probador,
      items: [
        {
          variante_id: this.varianteId,
          cantidad: qty,
          sku: variante?.sku || '',
          prenda_nombre: prenda?.nombre || 'Prenda Offline',
          talla: variante?.talla_nombre || '-',
          color: variante?.color_nombre || '-',
        },
      ],
    });
  }
}
