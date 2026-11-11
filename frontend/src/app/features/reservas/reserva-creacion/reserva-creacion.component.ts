import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';
import { AuthService } from '../../../core/auth.service';
import { CatalogoService } from '../../../core/catalogo.service';
import { InventarioService } from '../../../core/inventario.service';
import { DisponibilidadSucursal, Prenda, Variante } from '../../../core/models';
import { NetworkService } from '../../../core/network.service';
import { ReservaService } from '../../../core/reserva.service';

export const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function formatoDatetimeLocal(fecha: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${fecha.getFullYear()}-${pad(fecha.getMonth() + 1)}-${pad(fecha.getDate())}T${pad(fecha.getHours())}:${pad(fecha.getMinutes())}`;
}

export function extraerMensajeErrorReserva(err: any): string {
  const detail = err?.error?.detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item: any) => {
        const loc = Array.isArray(item?.loc) ? item.loc.join('.') : '';
        const msg = String(item?.msg || '');
        if (loc.includes('sucursal_id') && msg.toLowerCase().includes('uuid')) {
          return 'La sucursal debe seleccionarse de la lista o tener un UUID válido.';
        }
        if (loc.includes('variante_id') && msg.toLowerCase().includes('uuid')) {
          return 'La variante debe seleccionarse de la lista o tener un UUID válido.';
        }
        if (loc.includes('fecha_visita')) {
          return 'La fecha y hora de visita no es válida.';
        }
        return msg || 'Error de validación en los datos enviados.';
      })
      .join(' ');
  }
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
    return detail.message;
  }
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (err?.status === 401) {
    return 'Tu sesión ha expirado. Inicia sesión nuevamente.';
  }
  if (err?.status === 403) {
    return 'No tienes permisos para realizar esta reserva.';
  }
  return err?.message || 'No se pudo crear la reserva.';
}

@Component({
  selector: 'app-reserva-creacion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="res-page">
      <div class="res-tabs">
        <a routerLink="/reservas/nueva" class="res-tab active">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" class="res-tab">CU-20: Mis Reservas / Consulta</a>
        @if (esStaff()) {
          <a routerLink="/reservas/staff" class="res-tab">CU-21: Preparación Staff Tienda</a>
        }
      </div>

      <header class="res-header">
        <div>
          <span class="res-badge-tag">Reserva Presencial en Tienda</span>
          <h1 class="res-title">CU-19: Reserva de Prendas y Probador</h1>
          <p class="res-subtitle">Agenda tu visita para probarte prendas en tienda sin compromiso de compra</p>
        </div>
      </header>

      @if (!network.online()) {
        <div class="res-banner warning">
          <strong>Modo Sin Conexión:</strong> Estás usando el catálogo y existencias cacheadas localmente (CU-25 / IndexedDB). Al confirmar, tu reserva se guardará en la cola local (CU-26) y se sincronizará automáticamente al reconectar.
        </div>
      }

      @if (esStockLocal() && network.online()) {
        <div class="res-banner info">
          Mostrando disponibilidad estimada de caché local (CU-18 offline fallback).
        </div>
      }

      <div class="res-card">
        <div class="res-card-top">
          <span class="res-section-hint">Completa los datos de tu visita</span>
          <button
            type="button"
            (click)="toggleModoManual()"
            class="res-link-btn"
          >
            {{ modoManual() ? 'Usar selectores de catálogo' : 'Ingresar UUID manualmente' }}
          </button>
        </div>

        @if (cargandoCatalogo() && prendas().length === 0 && !modoManual()) {
          <div class="res-loading">
            <div class="res-spinner"></div>
            <span>Cargando catálogo y disponibilidad en sucursales...</span>
          </div>
        } @else {
          @if (!modoManual() && prendas().length > 0) {
            <div class="res-field">
              <label class="res-label" for="res-prenda">Prenda</label>
              <select
                id="res-prenda"
                [ngModel]="prendaSeleccionadaId()"
                (ngModelChange)="onPrendaChange($event)"
                class="res-control"
              >
                @for (p of prendas(); track p.id) {
                  <option [value]="p.id">{{ p.nombre }} ({{ p.codigo }}) — BOB {{ p.precio_base | number:'1.2-2' }}</option>
                }
              </select>
            </div>

            <div class="res-field">
              <label class="res-label" for="res-variante">Variante (Talla / Color)</label>
              <select
                id="res-variante"
                [ngModel]="varianteId()"
                (ngModelChange)="onVarianteChange($event)"
                class="res-control"
              >
                @for (v of variantesDisponibles(); track v.id) {
                  <option [value]="v.id">
                    {{ v.talla_nombre || 'Talla' }} / {{ v.color_nombre || 'Color' }} ({{ v.sku }})
                  </option>
                }
              </select>
            </div>
          } @else {
            <div class="res-field">
              <label class="res-label" for="res-variante-uuid">Variante a Probar (UUID)</label>
              <input
                id="res-variante-uuid"
                type="text"
                [ngModel]="varianteId()"
                (ngModelChange)="varianteId.set($event)"
                placeholder="Ej: 22222222-2222-2222-2222-222222222201"
                class="res-control mono"
              />
            </div>
          }

          @if (!modoManual() && sucursalesOpciones().length > 0) {
            <div class="res-field">
              <label class="res-label" for="res-sucursal">Sucursal de Visita</label>
              <select
                id="res-sucursal"
                [ngModel]="sucursalId()"
                (ngModelChange)="onSucursalChange($event)"
                class="res-control"
              >
                @for (s of sucursalesOpciones(); track s.id) {
                  <option [value]="s.id">
                    {{ s.nombre }}@if (s.ciudad) { ({{ s.ciudad }})} — {{ s.stockLabel }}
                  </option>
                }
              </select>
              @if (stockInsuficienteEnSeleccion()) {
                <div class="res-inline-warn">
                  ⚠️ Stock insuficiente para la cantidad solicitada en esta sucursal (disponible: {{ sucursalSeleccionada()?.stockQty ?? 0 }}). Elige otra sucursal o variante.
                </div>
              }
            </div>
          } @else {
            <div class="res-field">
              <label class="res-label" for="res-sucursal-uuid">Sucursal de Visita (UUID)</label>
              <input
                id="res-sucursal-uuid"
                type="text"
                [ngModel]="sucursalId()"
                (ngModelChange)="onSucursalChange($event)"
                placeholder="Ej: 11111111-1111-1111-1111-111111111101"
                class="res-control mono"
              />
            </div>
          }

          <div class="res-grid-2">
            <div class="res-field">
              <label class="res-label" for="res-cantidad">Cantidad</label>
              <input
                id="res-cantidad"
                type="number"
                min="1"
                max="20"
                [ngModel]="cantidad()"
                (ngModelChange)="cantidad.set(normalizarCantidad($event))"
                class="res-control"
              />
            </div>
            <div class="res-field">
              <label class="res-label" for="res-fecha">Fecha y Hora de Visita</label>
              <input
                id="res-fecha"
                type="datetime-local"
                [ngModel]="fechaVisita()"
                (ngModelChange)="fechaVisita.set($event)"
                class="res-control"
              />
            </div>
          </div>

          <label class="res-checkbox-row" for="probador">
            <input
              type="checkbox"
              id="probador"
              [ngModel]="requiereProbador()"
              (ngModelChange)="requiereProbador.set($event)"
            />
            <span>Apartar cabina de probador en tienda</span>
          </label>

          <button
            type="button"
            (click)="crear()"
            [disabled]="cargando() || !sucursalId().trim() || !varianteId().trim()"
            class="res-submit-btn"
          >
            {{ cargando() ? 'Procesando reserva...' : (network.online() ? 'Confirmar Reserva (CU-19)' : 'Guardar Reserva Offline (CU-26)') }}
          </button>

          @if (mensaje()) {
            <div
              class="res-alert"
              [class.error]="esError()"
              [class.warning]="!esError() && esOfflineResult()"
              [class.success]="!esError() && !esOfflineResult()"
              role="alert"
            >
              <div class="res-alert-msg">{{ mensaje() }}</div>
              @if (!esError()) {
                <div class="res-alert-links">
                  <a routerLink="/reservas/mis-reservas" class="res-alert-link">Ver Mis Reservas →</a>
                  @if (esOfflineResult()) {
                    <a routerLink="/offline/cola" class="res-alert-link">Ver Cola de Sync →</a>
                  }
                </div>
              }
            </div>
          }
        }
      </div>
    </div>
  `,
  styles: [`
    .res-page {
      max-width: 720px;
      margin: 0 auto;
      padding: 24px 16px 40px;
      color: #0f172a;
    }
    .res-tabs {
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
    .res-tab {
      padding: 0.45rem 0.9rem;
      border-radius: 9px;
      font-size: 0.86rem;
      font-weight: 600;
      color: #475569;
      text-decoration: none;
      transition: all 0.15s ease;
    }
    .res-tab:hover {
      background: #f8fafc;
      color: #0f172a;
    }
    .res-tab.active {
      background: #fdf2f8;
      color: #be185d;
      font-weight: 700;
    }
    .res-header {
      margin-bottom: 1.25rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .res-badge-tag {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #be185d;
      background: #fdf2f8;
      border: 1px solid #fbcfe8;
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      margin-bottom: 0.5rem;
    }
    .res-title {
      font-size: 1.65rem;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 0.35rem;
      letter-spacing: -0.02em;
    }
    .res-subtitle {
      margin: 0;
      font-size: 0.92rem;
      color: #64748b;
    }
    .res-banner {
      padding: 0.85rem 1rem;
      border-radius: 12px;
      font-size: 0.84rem;
      line-height: 1.45;
      margin-bottom: 1rem;
      border: 1px solid transparent;
    }
    .res-banner.warning {
      background: #fffbeb;
      border-color: #fde68a;
      color: #92400e;
    }
    .res-banner.info {
      background: #eff6ff;
      border-color: #bfdbfe;
      color: #1e40af;
    }
    .res-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 1.5rem;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .res-card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .res-section-hint {
      font-size: 0.82rem;
      font-weight: 600;
      color: #64748b;
    }
    .res-link-btn {
      background: transparent;
      border: 0;
      color: #4f46e5;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
      padding: 0.25rem 0.4rem;
      border-radius: 6px;
    }
    .res-link-btn:hover {
      background: #eef2ff;
      text-decoration: underline;
    }
    .res-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 2rem 1rem;
      color: #475569;
      font-size: 0.9rem;
      font-weight: 500;
    }
    .res-spinner {
      width: 22px;
      height: 22px;
      border: 3px solid #e2e8f0;
      border-top-color: #be185d;
      border-radius: 50%;
      animation: res-spin 0.8s linear infinite;
    }
    @keyframes res-spin {
      to { transform: rotate(360deg); }
    }
    .res-field {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .res-label {
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #334155;
    }
    .res-control {
      width: 100%;
      padding: 0.65rem 0.85rem;
      font-size: 0.92rem;
      color: #0f172a;
      background: #ffffff;
      border: 1.5px solid #cbd5e1;
      border-radius: 10px;
      font-family: inherit;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .res-control:focus {
      outline: none;
      border-color: #be185d;
      box-shadow: 0 0 0 3px rgba(190, 24, 93, 0.14);
    }
    .res-control.mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.85rem;
    }
    .res-inline-warn {
      margin-top: 0.3rem;
      padding: 0.55rem 0.75rem;
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    .res-grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
    }
    @media (max-width: 600px) {
      .res-grid-2 {
        grid-template-columns: 1fr;
      }
    }
    .res-checkbox-row {
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.9rem;
      font-weight: 500;
      color: #1e293b;
      cursor: pointer;
      user-select: none;
      padding: 0.25rem 0;
    }
    .res-checkbox-row input[type='checkbox'] {
      width: 18px;
      height: 18px;
      accent-color: #be185d;
      cursor: pointer;
    }
    .res-submit-btn {
      width: 100%;
      padding: 0.85rem 1.25rem;
      border: 0;
      border-radius: 12px;
      background: linear-gradient(135deg, #be185d 0%, #9d174d 100%);
      color: #ffffff;
      font-size: 0.95rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 6px 16px rgba(190, 24, 93, 0.24);
      transition: transform 0.12s ease, opacity 0.15s ease, box-shadow 0.15s ease;
    }
    .res-submit-btn:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 8px 20px rgba(190, 24, 93, 0.32);
    }
    .res-submit-btn:disabled {
      opacity: 0.52;
      cursor: not-allowed;
      box-shadow: none;
    }
    .res-alert {
      padding: 0.9rem 1rem;
      border-radius: 12px;
      border: 1px solid transparent;
      font-size: 0.86rem;
      font-weight: 600;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .res-alert.error {
      background: #fef2f2;
      border-color: #fecaca;
      color: #991b1b;
    }
    .res-alert.warning {
      background: #fffbeb;
      border-color: #fde68a;
      color: #92400e;
    }
    .res-alert.success {
      background: #ecfdf5;
      border-color: #a7f3d0;
      color: #065f46;
    }
    .res-alert-links {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .res-alert-link {
      color: inherit;
      font-weight: 700;
      text-decoration: underline;
    }
  `],
})
export class ReservaCreacionComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly auth = inject(AuthService);
  private readonly reservaService = inject(ReservaService);
  private readonly catalogoService = inject(CatalogoService);
  private readonly inventarioService = inject(InventarioService);
  private readonly cu25Offline = inject(CU25DescargarCatalogoOfflineController);
  readonly network = inject(NetworkService);

  esStaff = computed(() =>
    ['superadmin', 'administrador', 'encargado', 'cajero'].includes(this.auth.user()?.rol || ''),
  );

  prendas = signal<Prenda[]>([]);
  prendaSeleccionadaId = signal<string>('');
  disponibilidad = signal<DisponibilidadSucursal[]>([]);
  sucursalesCacheadas = signal<Array<{ id: string; nombre: string; ciudad?: string }>>([]);
  esStockLocal = signal(false);
  modoManual = signal(false);
  cargandoCatalogo = signal(false);

  sucursalId = signal<string>('');
  fechaVisita = signal<string>(formatoDatetimeLocal(new Date(Date.now() + 24 * 3600 * 1000)));
  requiereProbador = signal<boolean>(true);
  varianteId = signal<string>('');
  cantidad = signal<number>(1);

  cargando = signal(false);
  mensaje = signal<string | null>(null);
  esError = signal(false);
  esOfflineResult = signal(false);

  private sucursalSeleccionManual = false;

  constructor() {
    effect(() => {
      const cu25Sucs = this.cu25Offline.sucursalesList();
      if (cu25Sucs.length > 0 && this.sucursalesCacheadas().length === 0) {
        this.sucursalesCacheadas.set(cu25Sucs);
      }
      const opts = this.sucursalesOpciones();
      if (!this.sucursalId() && opts.length > 0) {
        this.sucursalId.set(opts[0].id);
      }
    });
  }

  variantesDisponibles = computed<Variante[]>(() => {
    const pid = this.prendaSeleccionadaId();
    const prenda = this.prendas().find((p) => p.id === pid);
    return prenda?.variantes || [];
  });

  sucursalesOpciones = computed(() => {
    const varId = this.varianteId();
    const disp = this.disponibilidad();
    const byId = new Map<
      string,
      { id: string; nombre: string; ciudad: string; stockQty: number; stockKnown: boolean; stockLabel: string }
    >();

    for (const s of disp) {
      const vars = s.variantes || [];
      const match = varId ? vars.find((v) => v.variante_id === varId) : null;
      const qty = match
        ? Number(match.stock_disponible || 0)
        : vars.reduce((acc, v) => acc + Number(v.stock_disponible || 0), 0);
      byId.set(s.sucursal_id, {
        id: s.sucursal_id,
        nombre: s.nombre,
        ciudad: s.ciudad || '',
        stockQty: qty,
        stockKnown: Boolean(match || vars.length > 0),
        stockLabel: `${qty} disp.${this.esStockLocal() ? ' (local)' : ''}`,
      });
    }

    const fallbackSucs = [
      ...this.cu25Offline.sucursalesList(),
      ...this.sucursalesCacheadas(),
    ];
    for (const s of fallbackSucs) {
      if (!byId.has(s.id)) {
        byId.set(s.id, {
          id: s.id,
          nombre: s.nombre,
          ciudad: s.ciudad || '',
          stockQty: 0,
          stockKnown: false,
          stockLabel: 'disponible según caché',
        });
      }
    }

    return Array.from(byId.values());
  });

  sucursalSeleccionada = computed(() =>
    this.sucursalesOpciones().find((s) => s.id === this.sucursalId()) ?? null,
  );

  stockInsuficienteEnSeleccion = computed(() => {
    const sel = this.sucursalSeleccionada();
    return Boolean(sel && sel.stockKnown && sel.stockQty < this.cantidad());
  });

  ngOnInit(): void {
    const qp = this.route.snapshot.queryParamMap;
    const qpPrenda = qp.get('prenda_id') || '';
    const qpVariante = qp.get('variante_id') || '';
    const qpSucursal = qp.get('sucursal_id') || '';
    const qpCantidad = Number(qp.get('cantidad') || 1);
    if (qpCantidad > 0) this.cantidad.set(Math.min(20, Math.floor(qpCantidad)));

    if (qpSucursal) {
      this.sucursalSeleccionManual = true;
      this.sucursalId.set(qpSucursal);
    }

    this.cu25Offline.asegurarCatalogoOfflineCargado();
    const sucCache = this.inventarioService.obtenerSucursalesOffline();
    this.sucursalesCacheadas.set(sucCache);
    if (!this.sucursalId() && sucCache.length > 0) {
      this.sucursalId.set(sucCache[0].id);
    }

    const locales = this.catalogoService.obtenerPrendasCacheadas();
    if (locales.length > 0) {
      this.inicializarPrendas(locales, qpPrenda, qpVariante);
    } else {
      this.cargandoCatalogo.set(true);
    }

    this.catalogoService.consultarCatalogo().subscribe({
      next: (res) => {
        this.cargandoCatalogo.set(false);
        const list = res.items.length > 0 ? res.items : locales;
        if (list.length > 0) {
          this.inicializarPrendas(
            list,
            qpPrenda || this.prendaSeleccionadaId(),
            qpVariante || this.varianteId(),
          );
        }
      },
      error: () => {
        this.cargandoCatalogo.set(false);
      },
    });
  }

  toggleModoManual(): void {
    this.modoManual.update((v) => !v);
    this.mensaje.set(null);
  }

  normalizarCantidad(val: any): number {
    const num = Math.floor(Number(val) || 1);
    return Math.min(20, Math.max(1, num));
  }

  private inicializarPrendas(list: Prenda[], preferredPrendaId: string, preferredVarianteId: string): void {
    this.prendas.set(list);
    let selectedPrenda = list.find((p) => p.id === preferredPrendaId);
    if (!selectedPrenda && preferredVarianteId) {
      selectedPrenda = list.find((p) => p.variantes?.some((v) => v.id === preferredVarianteId));
    }
    if (!selectedPrenda) {
      selectedPrenda = list[0];
    }
    if (!selectedPrenda) return;

    this.prendaSeleccionadaId.set(selectedPrenda.id);
    const variantes = selectedPrenda.variantes || [];
    if (preferredVarianteId && variantes.some((v) => v.id === preferredVarianteId)) {
      this.varianteId.set(preferredVarianteId);
    } else if (!this.varianteId() || !variantes.some((v) => v.id === this.varianteId())) {
      this.varianteId.set(variantes[0]?.id || '');
    }
    this.cargarDisponibilidadPrenda(selectedPrenda.id);
  }

  onPrendaChange(prendaId: string): void {
    this.prendaSeleccionadaId.set(prendaId);
    const vars = this.variantesDisponibles();
    this.varianteId.set(vars[0]?.id || '');
    this.cargarDisponibilidadPrenda(prendaId);
  }

  onVarianteChange(varId: string): void {
    this.varianteId.set(varId);
    if (!this.sucursalSeleccionManual) {
      this.autoseleccionarSucursalConStock();
    }
  }

  onSucursalChange(sucId: string): void {
    this.sucursalSeleccionManual = true;
    this.sucursalId.set(sucId);
  }

  private cargarDisponibilidadPrenda(prendaId: string): void {
    if (!prendaId) return;
    this.inventarioService.consultarDisponibilidad(prendaId).subscribe({
      next: (disp) => {
        this.disponibilidad.set(disp.sucursales || []);
        this.esStockLocal.set(Boolean(disp.es_local));
        if (!this.sucursalSeleccionManual) {
          this.autoseleccionarSucursalConStock();
        }
      },
      error: () => {},
    });
  }

  private autoseleccionarSucursalConStock(): void {
    const sucs = this.sucursalesOpciones();
    if (sucs.length === 0) return;

    const current = sucs.find((s) => s.id === this.sucursalId());
    if (current && current.stockKnown && current.stockQty >= this.cantidad()) {
      return;
    }
    const conSuficiente = sucs.find((s) => s.stockKnown && s.stockQty >= this.cantidad());
    if (conSuficiente) {
      this.sucursalId.set(conSuficiente.id);
      return;
    }
    const conAlgo = sucs.find((s) => s.stockKnown && s.stockQty > 0);
    if (conAlgo) {
      this.sucursalId.set(conAlgo.id);
      return;
    }
    if (!current) {
      this.sucursalId.set(sucs[0].id);
    }
  }

  crear(): void {
    const sucId = this.sucursalId().trim();
    const varId = this.varianteId().trim();

    if (!sucId || !varId) {
      this.esError.set(true);
      this.mensaje.set('Selecciona una sucursal y una variante válidas.');
      return;
    }

    if (!UUID_REGEX.test(sucId)) {
      this.esError.set(true);
      this.mensaje.set('La sucursal seleccionada no tiene un UUID válido. Elige una tienda de la lista desplegable.');
      return;
    }

    if (!UUID_REGEX.test(varId)) {
      this.esError.set(true);
      this.mensaje.set('La variante seleccionada no tiene un UUID válido. Elige una prenda y talla de la lista.');
      return;
    }

    const fechaObj = new Date(this.fechaVisita());
    if (!this.fechaVisita() || Number.isNaN(fechaObj.getTime()) || fechaObj.getTime() <= Date.now()) {
      this.esError.set(true);
      this.mensaje.set('La fecha y hora de visita debe ser posterior a la hora actual.');
      return;
    }

    this.cargando.set(true);
    this.mensaje.set(null);
    this.esError.set(false);
    this.esOfflineResult.set(false);

    const prenda = this.prendas().find((p) => p.id === this.prendaSeleccionadaId());
    const variante = this.variantesDisponibles().find((v) => v.id === varId);
    const sucOpt = this.sucursalesOpciones().find((s) => s.id === sucId);

    this.reservaService
      .crearReserva({
        sucursal_id: sucId,
        sucursal_nombre: sucOpt?.nombre || null,
        fecha_visita: fechaObj.toISOString(),
        probador: this.requiereProbador(),
        items: [
          {
            variante_id: varId,
            cantidad: this.normalizarCantidad(this.cantidad()),
            sku: variante?.sku || '',
            prenda_nombre: prenda?.nombre || 'Prenda',
            talla: variante?.talla_nombre || '-',
            color: variante?.color_nombre || '-',
          },
        ],
      })
      .subscribe({
        next: (res) => {
          this.cargando.set(false);
          if (res.offline) {
            this.esOfflineResult.set(true);
            this.mensaje.set(
              res.message ||
                `Sin conexión: reserva guardada localmente (${res.codigo}) y se sincronizará al volver la red.`,
            );
          } else {
            this.mensaje.set(`¡Reserva creada exitosamente! Código: ${res.codigo || res.id}`);
          }
        },
        error: (err: any) => {
          this.esError.set(true);
          this.mensaje.set(`Error: ${extraerMensajeErrorReserva(err)}`);
          this.cargando.set(false);
        },
      });
  }
}
