import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';
import { CU26RegistrarReservaOfflineController } from '../../../controller/cu26_registrar_reserva_offline_controller';
import { CU27BloquearStockSoftLockController } from '../../../controller/cu27_bloquear_stock_soft_lock_controller';
import { CatalogoService } from '../../../core/catalogo.service';
import { InventarioService } from '../../../core/inventario.service';
import { DisponibilidadSucursal, Prenda, Variante } from '../../../core/models';
import {
  UUID_REGEX,
  formatoDatetimeLocal,
} from '../../reservas/reserva-creacion/reserva-creacion.component';

@Component({
  selector: 'app-reserva-offline',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="ro-page">
      <div class="ro-tabs">
        <a routerLink="/offline/reserva" class="ro-tab active">CU-26: Reserva Offline</a>
        <a routerLink="/offline/bloqueos" class="ro-tab">
          CU-27: Bloqueos Activos ({{ softLockCtrl.bloqueos().length }})
        </a>
        <a routerLink="/offline/cola" class="ro-tab">CU-30/31: Cola y Sync</a>
      </div>

      <header class="ro-header">
        <span class="ro-badge-tag">Resiliencia Outbox • UUID v4</span>
        <h1 class="ro-title">CU-26: Registrar Reserva Offline</h1>
        <p class="ro-subtitle">Genera una reserva persistida en la cola local y opcionalmente aplica soft-lock temporal (CU-27)</p>
      </header>

      <div class="ro-banner warning">
        <strong>Modo Desconectado:</strong> La reserva se almacenará en la cola Outbox con identificador UUID v4 único y se sincronizará automáticamente al volver la conexión.
      </div>

      <div class="ro-card">
        <div class="ro-card-top">
          <span class="ro-section-hint">Datos de la reserva local</span>
          <button type="button" (click)="modoManual.set(!modoManual())" class="ro-link-btn">
            {{ modoManual() ? 'Usar catálogo cacheado' : 'Ingresar UUID manualmente' }}
          </button>
        </div>

        @if (!modoManual() && prendas().length > 0) {
          <div class="ro-field">
            <label class="ro-label" for="ro-prenda">Prenda en Caché</label>
            <select
              id="ro-prenda"
              [ngModel]="prendaSeleccionadaId()"
              (ngModelChange)="onPrendaChange($event)"
              class="ro-control"
            >
              @for (p of prendas(); track p.id) {
                <option [value]="p.id">{{ p.nombre }} ({{ p.codigo }})</option>
              }
            </select>
          </div>
          <div class="ro-field">
            <label class="ro-label" for="ro-variante">Variante (Talla / Color)</label>
            <select
              id="ro-variante"
              [ngModel]="varianteId()"
              (ngModelChange)="varianteId.set($event)"
              class="ro-control"
            >
              @for (v of variantesDisponibles(); track v.id) {
                <option [value]="v.id">{{ v.talla_nombre || 'Talla' }} / {{ v.color_nombre || 'Color' }} ({{ v.sku }})</option>
              }
            </select>
          </div>
        } @else {
          <div class="ro-field">
            <label class="ro-label" for="ro-variante-uuid">Variante ID (UUID)</label>
            <input
              id="ro-variante-uuid"
              [ngModel]="varianteId()"
              (ngModelChange)="varianteId.set($event)"
              placeholder="UUID de la variante"
              class="ro-control mono"
            />
          </div>
        }

        @if (!modoManual() && sucursalesOpciones().length > 0) {
          <div class="ro-field">
            <label class="ro-label" for="ro-sucursal">Sucursal</label>
            <select
              id="ro-sucursal"
              [ngModel]="sucursalId()"
              (ngModelChange)="sucursalId.set($event)"
              class="ro-control"
            >
              @for (s of sucursalesOpciones(); track s.id) {
                <option [value]="s.id">{{ s.nombre }}@if (s.ciudad) { ({{ s.ciudad }})} — {{ s.stockLabel }}</option>
              }
            </select>
          </div>
        } @else {
          <div class="ro-field">
            <label class="ro-label" for="ro-sucursal-uuid">Sucursal ID (UUID)</label>
            <input
              id="ro-sucursal-uuid"
              [ngModel]="sucursalId()"
              (ngModelChange)="sucursalId.set($event)"
              placeholder="UUID de la sucursal"
              class="ro-control mono"
            />
          </div>
        }

        <div class="ro-grid-2">
          <div class="ro-field">
            <label class="ro-label" for="ro-cantidad">Cantidad</label>
            <input
              id="ro-cantidad"
              type="number"
              min="1"
              max="20"
              [ngModel]="cantidad()"
              (ngModelChange)="cantidad.set(normalizarCantidad($event))"
              class="ro-control"
            />
          </div>
          <div class="ro-field">
            <label class="ro-label" for="ro-fecha">Fecha y Hora de Visita</label>
            <input
              id="ro-fecha"
              type="datetime-local"
              [ngModel]="fechaVisita()"
              (ngModelChange)="fechaVisita.set($event)"
              class="ro-control"
            />
          </div>
        </div>

        <label class="ro-checkbox-row" for="ro-probador">
          <input
            type="checkbox"
            id="ro-probador"
            [ngModel]="probador()"
            (ngModelChange)="probador.set($event)"
          />
          <span>Apartar cabina de probador</span>
        </label>

        <label class="ro-checkbox-row" for="ro-softlock">
          <input
            type="checkbox"
            id="ro-softlock"
            [ngModel]="aplicarSoftLock()"
            (ngModelChange)="aplicarSoftLock.set($event)"
          />
          <span>Aplicar Soft-Lock temporal de 45 min (CU-27)</span>
        </label>

        <button
          type="button"
          (click)="guardar()"
          [disabled]="!sucursalId().trim() || !varianteId().trim()"
          class="ro-submit-btn"
        >
          Guardar Reserva en Cola Outbox
        </button>

        @if (validacionError() || ctrl.error()) {
          <div class="ro-alert error" role="alert">
            {{ validacionError() || ctrl.error() }}
          </div>
        }

        @if (ctrl.reservaUuid(); as uuid) {
          <div class="ro-alert success" role="status">
            <span>Reserva registrada localmente ({{ ctrl.codigoLocal() || uuid.slice(0, 8) }}) • UUID: {{ uuid }}</span>
            <div class="ro-alert-links">
              <a routerLink="/reservas/mis-reservas">Mis Reservas →</a>
              <a routerLink="/offline/bloqueos">Bloqueos ({{ softLockCtrl.bloqueos().length }}) →</a>
              <a routerLink="/offline/cola">Cola de Sync →</a>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .ro-page {
      max-width: 720px;
      margin: 0 auto;
      padding: 24px 16px 40px;
      color: #0f172a;
    }
    .ro-tabs {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 1.5rem;
      background: #ffffff;
      padding: 0.65rem 0.85rem;
      border-radius: 14px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .ro-tab {
      padding: 0.45rem 0.9rem;
      border-radius: 9px;
      font-size: 0.86rem;
      font-weight: 600;
      color: #475569;
      text-decoration: none;
    }
    .ro-tab:hover { background: #f8fafc; color: #0f172a; }
    .ro-tab.active { background: #fdf2f8; color: #be185d; font-weight: 700; }
    .ro-header {
      margin-bottom: 1.25rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .ro-badge-tag {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #b45309;
      background: #fffbeb;
      border: 1px solid #fde68a;
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      margin-bottom: 0.45rem;
    }
    .ro-title { font-size: 1.65rem; font-weight: 800; margin: 0 0 0.3rem; }
    .ro-subtitle { margin: 0; font-size: 0.9rem; color: #64748b; }
    .ro-banner {
      padding: 0.85rem 1rem;
      border-radius: 12px;
      font-size: 0.84rem;
      line-height: 1.45;
      margin-bottom: 1rem;
      border: 1px solid transparent;
    }
    .ro-banner.warning { background: #fffbeb; border-color: #fde68a; color: #92400e; }
    .ro-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 1.5rem;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .ro-card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .ro-section-hint { font-size: 0.82rem; font-weight: 600; color: #64748b; }
    .ro-link-btn {
      background: transparent;
      border: 0;
      color: #4f46e5;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
      padding: 0.25rem 0.4rem;
      border-radius: 6px;
    }
    .ro-link-btn:hover { background: #eef2ff; text-decoration: underline; }
    .ro-field { display: flex; flex-direction: column; gap: 0.35rem; }
    .ro-label {
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #334155;
    }
    .ro-control {
      width: 100%;
      padding: 0.65rem 0.85rem;
      font-size: 0.92rem;
      color: #0f172a;
      background: #ffffff;
      border: 1.5px solid #cbd5e1;
      border-radius: 10px;
      font-family: inherit;
    }
    .ro-control:focus {
      outline: none;
      border-color: #4f46e5;
      box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.14);
    }
    .ro-control.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; }
    .ro-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
    @media (max-width: 600px) { .ro-grid-2 { grid-template-columns: 1fr; } }
    .ro-checkbox-row {
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.9rem;
      font-weight: 500;
      color: #1e293b;
      cursor: pointer;
    }
    .ro-checkbox-row input[type='checkbox'] {
      width: 18px;
      height: 18px;
      accent-color: #4f46e5;
      cursor: pointer;
    }
    .ro-submit-btn {
      width: 100%;
      padding: 0.85rem 1.25rem;
      border: 0;
      border-radius: 12px;
      background: #4f46e5;
      color: #ffffff;
      font-size: 0.95rem;
      font-weight: 700;
      cursor: pointer;
    }
    .ro-submit-btn:hover:not(:disabled) { background: #4338ca; }
    .ro-submit-btn:disabled { opacity: 0.52; cursor: not-allowed; }
    .ro-alert {
      padding: 0.9rem 1rem;
      border-radius: 12px;
      border: 1px solid transparent;
      font-size: 0.85rem;
      font-weight: 600;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .ro-alert.error { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
    .ro-alert.success { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
    .ro-alert-links { display: flex; gap: 1rem; flex-wrap: wrap; }
    .ro-alert-links a { color: inherit; font-weight: 700; text-decoration: underline; }
  `],
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
  validacionError = signal<string | null>(null);

  sucursalId = signal<string>('');
  varianteId = signal<string>('');
  cantidad = signal<number>(1);
  fechaVisita = signal<string>(formatoDatetimeLocal(new Date(Date.now() + 24 * 3600 * 1000)));
  probador = signal<boolean>(true);
  aplicarSoftLock = signal<boolean>(true);

  private qpSucursal = '';
  private qpVariante = '';
  private qpPrenda = '';

  constructor() {
    effect(() => {
      const cu25Sucs = this.cu25Offline.sucursalesList();
      if (cu25Sucs.length > 0 && this.sucursalesCacheadas().length === 0) {
        this.sucursalesCacheadas.set(cu25Sucs);
      }
      if (cu25Sucs.length > 0 && this.prendas().length === 0) {
        const locales = this.catalogoService.obtenerPrendasCacheadas();
        if (locales.length > 0) {
          this.inicializarPrendas(locales);
        }
      }
      if (this.prendas().length > 0 && this.sucursalesOpciones().length > 0 && this.modoManual()) {
        this.modoManual.set(false);
      }
      const opts = this.sucursalesOpciones();
      if (!this.sucursalId() && opts.length > 0) {
        this.sucursalId.set(opts[0].id);
      }
    });
  }

  variantesDisponibles = computed<Variante[]>(() => {
    const pid = this.prendaSeleccionadaId();
    return this.prendas().find((p) => p.id === pid)?.variantes || [];
  });

  sucursalesOpciones = computed(() => {
    const varId = this.varianteId();
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

    for (const s of [...this.cu25Offline.sucursalesList(), ...this.sucursalesCacheadas()]) {
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
    this.qpSucursal = qp.get('sucursal_id') || '';
    this.qpVariante = qp.get('variante_id') || '';
    this.qpPrenda = qp.get('prenda_id') || '';
    if (qp.get('cantidad')) this.cantidad.set(this.normalizarCantidad(qp.get('cantidad')));

    this.cu25Offline.asegurarCatalogoOfflineCargado();

    const sucs = this.inventarioService.obtenerSucursalesOffline();
    this.sucursalesCacheadas.set(sucs);
    if (this.qpSucursal) {
      this.sucursalId.set(this.qpSucursal);
    } else if (sucs.length > 0) {
      this.sucursalId.set(sucs[0].id);
    }

    const locales = this.catalogoService.obtenerPrendasCacheadas();
    if (locales.length > 0) {
      this.inicializarPrendas(locales);
    } else if (this.qpVariante) {
      this.varianteId.set(this.qpVariante);
    }

    if (this.prendas().length === 0 || (this.sucursalesCacheadas().length === 0 && this.cu25Offline.sucursalesList().length === 0)) {
      this.modoManual.set(true);
    }

    this.softLockCtrl.listarBloqueosActivos().subscribe();
  }

  private inicializarPrendas(locales: Prenda[]): void {
    this.prendas.set(locales);
    let prenda = locales.find((p) => p.id === this.qpPrenda);
    if (!prenda && this.qpVariante) {
      prenda = locales.find((p) => p.variantes?.some((v) => v.id === this.qpVariante));
    }
    prenda = prenda || locales[0];
    if (!prenda) return;

    this.prendaSeleccionadaId.set(prenda.id);
    const vars = prenda.variantes || [];
    const targetVar = this.qpVariante && vars.some((v) => v.id === this.qpVariante)
      ? this.qpVariante
      : vars[0]?.id || '';
    this.varianteId.set(targetVar);
    this.cargarDisponibilidadPrenda(prenda.id);
  }

  normalizarCantidad(val: any): number {
    return Math.min(20, Math.max(1, Math.floor(Number(val) || 1)));
  }

  onPrendaChange(prendaId: string): void {
    this.prendaSeleccionadaId.set(prendaId);
    const vars = this.variantesDisponibles();
    this.varianteId.set(vars[0]?.id || '');
    this.cargarDisponibilidadPrenda(prendaId);
  }

  private cargarDisponibilidadPrenda(prendaId: string): void {
    this.inventarioService.consultarDisponibilidad(prendaId).subscribe({
      next: (disp) => this.disponibilidad.set(disp.sucursales || []),
      error: () => {},
    });
  }

  guardar() {
    const sucId = this.sucursalId().trim();
    const varId = this.varianteId().trim();
    const fechaObj = new Date(this.fechaVisita());

    if (!UUID_REGEX.test(sucId) || !UUID_REGEX.test(varId)) {
      this.validacionError.set('Selecciona o ingresa un UUID válido tanto para la sucursal como para la variante.');
      return;
    }
    if (!this.fechaVisita() || Number.isNaN(fechaObj.getTime()) || fechaObj.getTime() <= Date.now()) {
      this.validacionError.set('La fecha y hora de visita debe ser posterior a la hora actual.');
      return;
    }

    this.validacionError.set(null);
    const qty = this.normalizarCantidad(this.cantidad());
    const prenda = this.prendas().find((p) => p.id === this.prendaSeleccionadaId());
    const variante = this.variantesDisponibles().find((v) => v.id === varId);
    const sucursal = this.sucursalesOpciones().find((s) => s.id === sucId);

    if (this.aplicarSoftLock() && sucId && varId) {
      this.softLockCtrl.bloquearStock(varId, qty, 45, sucId);
    }

    this.ctrl.registrarReserva({
      sucursal_id: sucId,
      sucursal_nombre: sucursal?.nombre || null,
      fecha_visita: fechaObj.toISOString(),
      probador: this.probador(),
      items: [
        {
          variante_id: varId,
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
