import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CU25DescargarCatalogoOfflineController } from '../../controller/cu25_descargar_catalogo_offline_controller';
import { CU31SincronizarOperacionesController } from '../../controller/cu31_sincronizar_operaciones_controller';
import { AuthService } from '../../core/auth.service';
import { CatalogoService } from '../../core/catalogo.service';
import { InventarioService } from '../../core/inventario.service';
import { Prenda, Reserva, Variante } from '../../core/models';
import { NetworkService } from '../../core/network.service';
import { ReservaService } from '../../core/reserva.service';
import {
  UUID_REGEX,
  extraerMensajeErrorReserva,
  formatoDatetimeLocal,
} from './reserva-creacion/reserva-creacion.component';

@Component({
  selector: 'app-reservas',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="reservas-page">
      <div class="header">
        <h2>Gestión y Consulta de Reservas</h2>
        <div class="tab-buttons">
          <button class="btn" [class.btn-primary]="tab === 'mis'" (click)="setTab('mis')">CU-20: Mis Reservas</button>
          <button *ngIf="esStaff" class="btn" [class.btn-primary]="tab === 'preparar'" (click)="setTab('preparar')">CU-21: Por Preparar (Staff)</button>
          <button *ngIf="pendientesOfflineCount > 0 && network.online()" class="btn btn-success" (click)="sincronizarPendientes()">
            ↻ Sincronizar ({{ pendientesOfflineCount }})
          </button>
          <button class="btn btn-outline" (click)="abrirModalNueva()">+ CU-19: Nueva Reserva</button>
        </div>
      </div>

      <div *ngIf="!network.online()" class="alert alert-offline">
        📡 Modo sin conexión activo: puedes consultar tus reservas guardadas y crear nuevas reservas en cola local (CU-26).
      </div>
      <div *ngIf="mensajeError" class="alert alert-error">{{ mensajeError }}</div>
      <div *ngIf="mensajeExito" class="alert alert-success">{{ mensajeExito }}</div>

      <!-- Lista de Reservas -->
      <div class="reservas-grid">
        <div *ngFor="let r of reservas" class="reserva-card">
          <div class="card-header">
            <span class="codigo">{{ r.codigo }}</span>
            <span class="badge" [ngClass]="'badge-' + r.estado">{{ r.estado }}</span>
          </div>

          <div class="card-body">
            <p><strong>Sucursal:</strong> {{ r.sucursal_nombre || r.sucursal_id }}</p>
            <p><strong>Visita programada:</strong> {{ r.fecha_visita | date:'short' }}</p>
            <p *ngIf="r.probador"><strong>Probador asignado:</strong> {{ r.probador }}</p>

            <div class="items-list">
              <h5>Prendas Apartadas:</h5>
              <ul>
                <li *ngFor="let it of r.items">
                  {{ it.prenda_nombre }} ({{ it.talla }} / {{ it.color }}) - Cant: {{ it.cantidad }}
                  <span *ngIf="it.ubicacion" class="ubicacion-tag">📍 {{ it.ubicacion }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="card-actions">
            <button *ngIf="r.estado === 'pendiente_preparacion' || r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync'"
                    class="btn btn-danger btn-sm"
                    (click)="cancelarReserva(r.id)">
              {{ r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync' ? 'Eliminar Pendiente' : 'Cancelar Reserva' }}
            </button>

            <ng-container *ngIf="esStaff && tab === 'preparar' && r.estado === 'pendiente_preparacion'">
              <button class="btn btn-success btn-sm" (click)="prepararReserva(r.id)">
                ✓ Marcar Preparada
              </button>
              <button class="btn btn-warning btn-sm" (click)="reportarIncidencia(r.id)">
                ⚠️ Reportar Incidencia
              </button>
            </ng-container>
          </div>
        </div>

        <div *ngIf="reservas.length === 0" class="empty-state">
          No hay reservas en esta bandeja.
        </div>
      </div>

      <!-- Modal Nueva Reserva (CU-19) -->
      <div class="modal-backdrop" *ngIf="mostrarModalNueva">
        <div class="modal-card">
          <h3>Realizar Reserva de Prendas (Prueba Presencial)</h3>
          <div *ngIf="modalError" class="alert alert-error">{{ modalError }}</div>
          <form [formGroup]="reservaForm" (ngSubmit)="guardarReserva()">
            <div class="form-group" *ngIf="prendasCache.length > 0">
              <label>Prenda</label>
              <select class="form-control" [value]="prendaSeleccionadaId" (change)="onPrendaSeleccionada($event)">
                <option *ngFor="let p of prendasCache" [value]="p.id">{{ p.nombre }} ({{ p.codigo }})</option>
              </select>
            </div>
            <div class="form-group">
              <label>Sucursal Destino</label>
              <select *ngIf="sucursalesCache.length > 0; else manualSuc" formControlName="sucursal_id" class="form-control">
                <option *ngFor="let s of sucursalesCache" [value]="s.id">{{ s.nombre }} <ng-container *ngIf="s.ciudad">({{ s.ciudad }})</ng-container></option>
              </select>
              <ng-template #manualSuc>
                <input formControlName="sucursal_id" class="form-control" placeholder="UUID de la Sucursal" />
              </ng-template>
            </div>
            <div class="form-group">
              <label>Fecha y Hora Tentativa de Visita</label>
              <input type="datetime-local" formControlName="fecha_visita" class="form-control" />
            </div>
            <div class="form-group">
              <label>Variante (Prenda/Talla/Color)</label>
              <select *ngIf="variantesPrendaActual.length > 0; else manualVar" formControlName="variante_id" class="form-control">
                <option *ngFor="let v of variantesPrendaActual" [value]="v.id">{{ v.talla_nombre || 'Talla' }} / {{ v.color_nombre || 'Color' }} ({{ v.sku }})</option>
              </select>
              <ng-template #manualVar>
                <input formControlName="variante_id" class="form-control" placeholder="UUID de la variante" />
              </ng-template>
            </div>
            <div class="form-group">
              <label>Cantidad</label>
              <input type="number" formControlName="cantidad" class="form-control" min="1" max="20" />
            </div>

            <div class="modal-actions">
              <button type="button" class="btn btn-outline" (click)="mostrarModalNueva = false">Cerrar</button>
              <button type="submit" class="btn btn-primary" [disabled]="reservaForm.invalid">Confirmar Reserva</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .reservas-page { padding: 24px; font-family: inherit; max-width: 1200px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .tab-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
    .btn { padding: 8px 14px; border-radius: 8px; border: 1px solid transparent; cursor: pointer; font-size: 0.88rem; font-weight: 600; }
    .btn-primary { background: #be185d; color: #fff; }
    .btn-outline { border-color: #cbd5e1; background: #fff; color: #334155; }
    .btn-danger { background: #ef4444; color: #fff; }
    .btn-success { background: #10b981; color: #fff; }
    .btn-warning { background: #f59e0b; color: #fff; }
    .btn-sm { padding: 5px 10px; font-size: 0.8rem; }
    .reservas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
    .reserva-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); }
    .card-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
    .codigo { font-weight: 700; color: #1e293b; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .badge { padding: 3px 8px; border-radius: 12px; font-size: 0.72rem; text-transform: uppercase; font-weight: 600; }
    .badge-pendiente_preparacion { background: #fef3c7; color: #b45309; }
    .badge-pendiente_sync { background: #fef3c7; color: #92400e; }
    .badge-conflicto_sync { background: #fee2e2; color: #991b1b; }
    .badge-preparada { background: #dcfce7; color: #15803d; }
    .badge-cancelada { background: #f1f5f9; color: #64748b; }
    .badge-incidencia_stock { background: #fee2e2; color: #b91c1c; }
    .card-body p { margin: 4px 0; font-size: 0.85rem; }
    .items-list h5 { margin: 8px 0 4px; font-size: 0.82rem; }
    .items-list ul { margin: 0; padding-left: 18px; font-size: 0.82rem; color: #475569; }
    .ubicacion-tag { background: #e0f2fe; color: #0369a1; padding: 1px 4px; border-radius: 3px; font-size: 0.75rem; }
    .card-actions { display: flex; gap: 8px; margin-top: 14px; border-top: 1px solid #f1f5f9; padding-top: 10px; }
    .empty-state { grid-column: 1 / -1; background: #fff; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 32px; text-align: center; color: #64748b; }
    .alert { padding: 10px 14px; border-radius: 10px; margin-bottom: 16px; font-size: 0.88rem; font-weight: 600; }
    .alert-offline { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .alert-success { background: #dcfce7; color: #166534; border: 1px solid #a7f3d0; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55); display: flex; align-items: center; justify-content: center; z-index: 60; padding: 16px; }
    .modal-card { background: #fff; padding: 24px; border-radius: 16px; width: 460px; max-width: 95vw; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 50px rgba(0,0,0,0.2); }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #334155; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 9px 10px; border: 1.5px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.9rem; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `],
})
export class ReservasComponent implements OnInit {
  reservas: Reserva[] = [];
  tab: 'mis' | 'preparar' = 'mis';
  mensajeError = '';
  mensajeExito = '';
  modalError = '';
  mostrarModalNueva = false;
  reservaForm: FormGroup;

  prendasCache: Prenda[] = [];
  sucursalesCache: Array<{ id: string; nombre: string; ciudad?: string }> = [];
  prendaSeleccionadaId = '';
  variantesPrendaActual: Variante[] = [];

  constructor(
    private readonly auth: AuthService,
    private readonly reservaService: ReservaService,
    private readonly catalogoService: CatalogoService,
    private readonly inventarioService: InventarioService,
    private readonly cu25Offline: CU25DescargarCatalogoOfflineController,
    private readonly syncCtrl: CU31SincronizarOperacionesController,
    readonly network: NetworkService,
    private readonly fb: FormBuilder,
  ) {
    this.reservaForm = this.fb.group({
      sucursal_id: ['', Validators.required],
      fecha_visita: [formatoDatetimeLocal(new Date(Date.now() + 24 * 3600 * 1000)), Validators.required],
      variante_id: ['', Validators.required],
      cantidad: [1, [Validators.required, Validators.min(1), Validators.max(20)]],
    });
  }

  get esStaff(): boolean {
    return ['superadmin', 'administrador', 'encargado', 'cajero'].includes(this.auth.user()?.rol || '');
  }

  get pendientesOfflineCount(): number {
    return this.reservas.filter((r) => r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync').length;
  }

  ngOnInit(): void {
    this.cu25Offline.asegurarCatalogoOfflineCargado();
    this.cargarSelectoresLocales();
    this.cargarReservas();
  }

  private cargarSelectoresLocales(): void {
    const cu25Sucs = this.cu25Offline.sucursalesList();
    this.sucursalesCache =
      cu25Sucs.length > 0 ? cu25Sucs : this.inventarioService.obtenerSucursalesOffline();
    if (this.sucursalesCache.length > 0 && !this.reservaForm.value.sucursal_id) {
      this.reservaForm.patchValue({ sucursal_id: this.sucursalesCache[0].id });
    }
    this.prendasCache = this.catalogoService.obtenerPrendasCacheadas();
    if (this.prendasCache.length > 0 && !this.prendaSeleccionadaId) {
      this.seleccionarPrenda(this.prendasCache[0].id);
    }
  }

  private seleccionarPrenda(prendaId: string): void {
    this.prendaSeleccionadaId = prendaId;
    const prenda = this.prendasCache.find((p) => p.id === prendaId);
    this.variantesPrendaActual = prenda?.variantes || [];
    if (this.variantesPrendaActual.length > 0) {
      this.reservaForm.patchValue({ variante_id: this.variantesPrendaActual[0].id });
    }
  }

  onPrendaSeleccionada(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.seleccionarPrenda(value);
  }

  setTab(nuevaTab: 'mis' | 'preparar'): void {
    if (nuevaTab === 'preparar' && !this.esStaff) return;
    this.tab = nuevaTab;
    this.cargarReservas();
  }

  cargarReservas(): void {
    this.mensajeError = '';
    if (this.tab === 'mis') {
      this.reservaService.listarReservas().subscribe({
        next: (resp) => (this.reservas = resp.items),
        error: (err) => (this.mensajeError = extraerMensajeErrorReserva(err)),
      });
    } else {
      this.reservaService.listarPorPreparar().subscribe({
        next: (resp) => (this.reservas = resp.items),
        error: (err) => (this.mensajeError = extraerMensajeErrorReserva(err)),
      });
    }
  }

  sincronizarPendientes(): void {
    this.syncCtrl.sincronizarLote().subscribe({
      next: (res) => {
        const ok = (res?.confirmados || []).length;
        const conf = (res?.conflictos || []).length;
        this.mensajeExito = `Sincronización completa: ${ok} confirmada(s), ${conf} con conflicto.`;
        this.cargarReservas();
      },
      error: (err) => {
        this.mensajeError = extraerMensajeErrorReserva(err);
      },
    });
  }

  cancelarReserva(id: string): void {
    if (!confirm('¿Confirma que desea cancelar esta reserva? El stock se liberará de inmediato.')) return;

    this.reservaService.cancelarReserva(id).subscribe({
      next: () => {
        this.mensajeExito = 'Reserva cancelada con éxito';
        this.cargarReservas();
      },
      error: (err) => (this.mensajeError = extraerMensajeErrorReserva(err)),
    });
  }

  prepararReserva(id: string): void {
    const probador = prompt('Ingrese el identificador del probador asignado (ej. Probador 1):') || 'Probador General';
    this.reservaService.prepararReserva(id, probador).subscribe({
      next: () => {
        this.mensajeExito = 'Reserva marcada como preparada. Cliente notificado.';
        this.cargarReservas();
      },
      error: (err) => (this.mensajeError = extraerMensajeErrorReserva(err)),
    });
  }

  reportarIncidencia(id: string): void {
    const motivo = prompt('Motivo de la incidencia (prenda dañada, extraviada):');
    if (!motivo) return;

    this.reservaService.reportarIncidencia(id, { variante_ids: [], motivo }).subscribe({
      next: () => {
        this.mensajeExito = 'Incidencia registrada. Se han generado alternativas para el cliente.';
        this.cargarReservas();
      },
      error: (err) => (this.mensajeError = extraerMensajeErrorReserva(err)),
    });
  }

  abrirModalNueva(): void {
    this.cargarSelectoresLocales();
    const fechaActual = new Date(this.reservaForm.value.fecha_visita || '');
    if (Number.isNaN(fechaActual.getTime()) || fechaActual.getTime() <= Date.now()) {
      this.reservaForm.patchValue({
        fecha_visita: formatoDatetimeLocal(new Date(Date.now() + 24 * 3600 * 1000)),
      });
    }
    this.modalError = '';
    this.mensajeError = '';
    this.mostrarModalNueva = true;

    if (this.network.online()) {
      if (this.prendasCache.length === 0) {
        this.catalogoService.consultarCatalogo().subscribe({
          next: (res) => {
            if (res.items.length > 0) {
              this.prendasCache = res.items;
              this.seleccionarPrenda(res.items[0].id);
            }
          },
          error: () => {},
        });
      }
      if (this.sucursalesCache.length === 0) {
        this.cu25Offline.descargarCatalogo().subscribe({
          next: () => this.cargarSelectoresLocales(),
          error: () => {},
        });
      }
    }
  }

  guardarReserva(): void {
    const val = this.reservaForm.value;
    const sucId = String(val.sucursal_id || '').trim();
    const varId = String(val.variante_id || '').trim();
    const fechaObj = new Date(val.fecha_visita);

    if (!UUID_REGEX.test(sucId) || !UUID_REGEX.test(varId)) {
      this.modalError = 'Selecciona una sucursal y una variante con UUID válido.';
      return;
    }
    if (!val.fecha_visita || Number.isNaN(fechaObj.getTime()) || fechaObj.getTime() <= Date.now()) {
      this.modalError = 'La fecha y hora de visita debe ser posterior a la hora actual.';
      return;
    }

    this.modalError = '';
    const prenda = this.prendasCache.find((p) => p.id === this.prendaSeleccionadaId);
    const variante = this.variantesPrendaActual.find((v) => v.id === varId);
    const sucursal = this.sucursalesCache.find((s) => s.id === sucId);

    this.reservaService
      .crearReserva({
        sucursal_id: sucId,
        sucursal_nombre: sucursal?.nombre || null,
        fecha_visita: fechaObj.toISOString(),
        items: [
          {
            variante_id: varId,
            cantidad: Math.min(20, Math.max(1, Math.floor(Number(val.cantidad) || 1))),
            sku: variante?.sku || '',
            prenda_nombre: prenda?.nombre || 'Prenda',
            talla: variante?.talla_nombre || '-',
            color: variante?.color_nombre || '-',
          },
        ],
      })
      .subscribe({
        next: (res) => {
          this.mensajeExito = res.offline
            ? res.message || `Reserva guardada offline (${res.codigo}).`
            : `Reserva creada exitosamente con código digital: ${res.codigo}`;
          this.mostrarModalNueva = false;
          this.cargarReservas();
        },
        error: (err) => {
          this.modalError = err?.offline ? err.message : extraerMensajeErrorReserva(err);
        },
      });
  }
}
