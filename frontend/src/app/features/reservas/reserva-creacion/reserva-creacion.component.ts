import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';
import { CatalogoService } from '../../../core/catalogo.service';
import { InventarioService } from '../../../core/inventario.service';
import { DisponibilidadSucursal, Prenda, Variante } from '../../../core/models';
import { NetworkService } from '../../../core/network.service';
import { ReservaService } from '../../../core/reserva.service';

@Component({
  selector: 'app-reserva-creacion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-2xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/reservas/nueva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-20: Mis Reservas / Consulta</a>
        <a routerLink="/reservas/staff" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-21: Preparación Staff Tienda</a>
      </div>

      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-19: Reserva de Prendas y Probador</h1>
        <p class="text-sm text-gray-500">Agenda tu visita para probarte prendas en tienda sin compromiso de compra</p>
      </div>

      @if (!network.online()) {
        <div class="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900">
          <strong>Modo Sin Conexión:</strong> Estás usando el catálogo y existencias cacheadas localmente (CU-25 / IndexedDB). Al confirmar, tu reserva se guardará en la cola local (CU-26) y se sincronizará automáticamente al reconectar.
        </div>
      }

      @if (esStockLocal() && network.online()) {
        <div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-xs text-yellow-800">
          Mostrando disponibilidad estimada de caché local (CU-18 offline fallback).
        </div>
      }

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div class="flex justify-end">
          <button
            type="button"
            (click)="modoManual.set(!modoManual())"
            class="text-xs font-semibold text-indigo-600 hover:underline"
          >
            {{ modoManual() ? 'Usar selectores de catálogo' : 'Ingresar UUID manualmente' }}
          </button>
        </div>

        @if (!modoManual() && prendas().length > 0) {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Prenda</label>
            <select
              [ngModel]="prendaSeleccionadaId()"
              (ngModelChange)="onPrendaChange($event)"
              class="w-full text-sm px-3 py-2 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500"
            >
              @for (p of prendas(); track p.id) {
                <option [value]="p.id">{{ p.nombre }} ({{ p.codigo }}) — BOB {{ p.precio_base | number:'1.2-2' }}</option>
              }
            </select>
          </div>

          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Variante (Talla / Color)</label>
            <select
              [(ngModel)]="varianteId"
              class="w-full text-sm px-3 py-2 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500"
            >
              @for (v of variantesDisponibles(); track v.id) {
                <option [value]="v.id">
                  {{ v.talla_nombre || 'Talla' }} / {{ v.color_nombre || 'Color' }} ({{ v.sku }})
                </option>
              }
            </select>
          </div>
        } @else {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Variante a Probar (UUID)</label>
            <input
              type="text"
              [(ngModel)]="varianteId"
              placeholder="UUID de la variante..."
              class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        }

        @if (!modoManual() && sucursalesOpciones().length > 0) {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Sucursal de Visita</label>
            <select
              [(ngModel)]="sucursalId"
              class="w-full text-sm px-3 py-2 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500"
            >
              @for (s of sucursalesOpciones(); track s.id) {
                <option [value]="s.id">
                  {{ s.nombre }}@if (s.ciudad) { ({{ s.ciudad }})} — {{ s.stockLabel }}
                </option>
              }
            </select>
          </div>
        } @else {
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Sucursal de Visita (UUID)</label>
            <input
              type="text"
              [(ngModel)]="sucursalId"
              placeholder="UUID de la Sucursal..."
              class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        }

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Cantidad</label>
            <input
              type="number"
              min="1"
              [(ngModel)]="cantidad"
              class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Fecha y Hora de Visita</label>
            <input
              type="datetime-local"
              [(ngModel)]="fechaVisita"
              class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input type="checkbox" id="probador" [(ngModel)]="requiereProbador" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="probador" class="text-sm text-gray-700 font-medium">Apartar cabina de probador</label>
        </div>

        <button
          (click)="crear()"
          [disabled]="cargando() || !sucursalId || !varianteId"
          class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition disabled:opacity-50"
        >
          {{ cargando() ? 'Procesando reserva...' : (network.online() ? 'Confirmar Reserva (CU-19)' : 'Guardar Reserva Offline (CU-26)') }}
        </button>

        @if (mensaje()) {
          <div
            [class]="esError() ? 'bg-red-50 text-red-800 border-red-200' : esOfflineResult() ? 'bg-amber-50 text-amber-900 border-amber-200' : 'bg-green-50 text-green-800 border-green-200'"
            class="p-3 border rounded-xl text-xs font-semibold space-y-2"
          >
            <div>{{ mensaje() }}</div>
            @if (!esError()) {
              <div class="flex gap-3">
                <a routerLink="/reservas/mis-reservas" class="underline font-bold">Ver Mis Reservas</a>
                @if (esOfflineResult()) {
                  <a routerLink="/offline/cola" class="underline font-bold">Ver Cola de Sync</a>
                }
              </div>
            }
          </div>
        }
      </div>
    </div>
  `
})
export class ReservaCreacionComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly reservaService = inject(ReservaService);
  private readonly catalogoService = inject(CatalogoService);
  private readonly inventarioService = inject(InventarioService);
  private readonly cu25Offline = inject(CU25DescargarCatalogoOfflineController);
  readonly network = inject(NetworkService);

  prendas = signal<Prenda[]>([]);
  prendaSeleccionadaId = signal<string>('');
  disponibilidad = signal<DisponibilidadSucursal[]>([]);
  sucursalesCacheadas = signal<Array<{ id: string; nombre: string; ciudad?: string }>>([]);
  esStockLocal = signal(false);
  modoManual = signal(false);

  sucursalId = '';
  fechaVisita = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 16);
  requiereProbador = true;
  varianteId = '';
  cantidad = 1;

  cargando = signal(false);
  mensaje = signal<string | null>(null);
  esError = signal(false);
  esOfflineResult = signal(false);

  variantesDisponibles = computed<Variante[]>(() => {
    const pid = this.prendaSeleccionadaId();
    const prenda = this.prendas().find((p) => p.id === pid);
    return prenda?.variantes || [];
  });

  sucursalesOpciones = computed(() => {
    const varId = this.varianteId;
    const disp = this.disponibilidad();
    const byId = new Map<string, { id: string; nombre: string; ciudad: string; stockLabel: string }>();

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
        stockLabel: `${qty} disp.${this.esStockLocal() ? ' (local)' : ''}`,
      });
    }

    for (const s of this.sucursalesCacheadas()) {
      if (!byId.has(s.id)) {
        byId.set(s.id, {
          id: s.id,
          nombre: s.nombre,
          ciudad: s.ciudad || '',
          stockLabel: 'disponible según caché',
        });
      }
    }

    return Array.from(byId.values());
  });

  ngOnInit(): void {
    const qp = this.route.snapshot.queryParamMap;
    const qpPrenda = qp.get('prenda_id') || '';
    const qpVariante = qp.get('variante_id') || '';
    const qpSucursal = qp.get('sucursal_id') || '';
    const qpCantidad = Number(qp.get('cantidad') || 1);
    if (qpCantidad > 0) this.cantidad = qpCantidad;

    this.cu25Offline.asegurarCatalogoOfflineCargado();
    const sucCache = this.inventarioService.obtenerSucursalesOffline();
    this.sucursalesCacheadas.set(sucCache);
    if (qpSucursal) {
      this.sucursalId = qpSucursal;
    } else if (sucCache.length > 0) {
      this.sucursalId = sucCache[0].id;
    }

    const locales = this.catalogoService.obtenerPrendasCacheadas();
    if (locales.length > 0) {
      this.inicializarPrendas(locales, qpPrenda, qpVariante);
    }

    this.catalogoService.consultarCatalogo().subscribe({
      next: (res) => {
        const list = res.items.length > 0 ? res.items : locales;
        if (list.length > 0) {
          this.inicializarPrendas(list, qpPrenda || this.prendaSeleccionadaId(), qpVariante || this.varianteId);
        }
      },
      error: () => {},
    });
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
      this.varianteId = preferredVarianteId;
    } else if (!this.varianteId || !variantes.some((v) => v.id === this.varianteId)) {
      this.varianteId = variantes[0]?.id || '';
    }
    this.cargarDisponibilidadPrenda(selectedPrenda.id);
  }

  onPrendaChange(prendaId: string): void {
    this.prendaSeleccionadaId.set(prendaId);
    const vars = this.variantesDisponibles();
    this.varianteId = vars[0]?.id || '';
    this.cargarDisponibilidadPrenda(prendaId);
  }

  private cargarDisponibilidadPrenda(prendaId: string): void {
    if (!prendaId) return;
    this.inventarioService.consultarDisponibilidad(prendaId).subscribe({
      next: (disp) => {
        this.disponibilidad.set(disp.sucursales || []);
        this.esStockLocal.set(Boolean(disp.es_local));
        const sucs = this.sucursalesOpciones();
        if (sucs.length > 0 && (!this.sucursalId || !sucs.some((s) => s.id === this.sucursalId))) {
          const conStock = this.disponibilidad().find((s) =>
            (s.variantes || []).some((v) => v.stock_disponible > 0 && (!this.varianteId || v.variante_id === this.varianteId)),
          );
          this.sucursalId = conStock?.sucursal_id || sucs[0].id;
        }
      },
      error: () => {},
    });
  }

  crear(): void {
    if (!this.sucursalId || !this.varianteId) {
      this.esError.set(true);
      this.mensaje.set('Selecciona una sucursal y una variante válidas.');
      return;
    }

    this.cargando.set(true);
    this.mensaje.set(null);
    this.esError.set(false);
    this.esOfflineResult.set(false);

    const prenda = this.prendas().find((p) => p.id === this.prendaSeleccionadaId());
    const variante = this.variantesDisponibles().find((v) => v.id === this.varianteId);
    const sucOpt = this.sucursalesOpciones().find((s) => s.id === this.sucursalId);

    this.reservaService
      .crearReserva({
        sucursal_id: this.sucursalId,
        sucursal_nombre: sucOpt?.nombre || null,
        fecha_visita: new Date(this.fechaVisita).toISOString(),
        probador: this.requiereProbador,
        items: [
          {
            variante_id: this.varianteId,
            cantidad: Math.max(1, Number(this.cantidad) || 1),
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
          this.mensaje.set(
            `Error: ${err?.error?.detail?.message || err?.error?.detail || err?.message || 'No se pudo crear la reserva'}`,
          );
          this.cargando.set(false);
        },
      });
  }
}

