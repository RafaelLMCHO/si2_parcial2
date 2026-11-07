import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Reserva } from '../../core/models';
import { ReservaService } from '../../core/reserva.service';

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
          <button class="btn" [class.btn-primary]="tab === 'preparar'" (click)="setTab('preparar')">CU-21: Por Preparar (Staff)</button>
          <button class="btn btn-outline" (click)="abrirModalNueva()">+ CU-19: Nueva Reserva</button>
        </div>
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
            <!-- Botón Cancelar (CU-20: solo si pendiente_preparacion) -->
            <button *ngIf="r.estado === 'pendiente_preparacion'" 
                    class="btn btn-danger btn-sm" 
                    (click)="cancelarReserva(r.id)">
              Cancelar Reserva
            </button>

            <!-- Acciones de Encargado (CU-21: Preparar o Reportar Incidencia) -->
            <ng-container *ngIf="tab === 'preparar' && r.estado === 'pendiente_preparacion'">
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
          <form [formGroup]="reservaForm" (ngSubmit)="guardarReserva()">
            <div class="form-group">
              <label>Sucursal Destino</label>
              <input formControlName="sucursal_id" class="form-control" placeholder="UUID de la Sucursal" />
            </div>
            <div class="form-group">
              <label>Fecha y Hora Tentativa de Visita</label>
              <input type="datetime-local" formControlName="fecha_visita" class="form-control" />
            </div>
            <div class="form-group">
              <label>Variante (Prenda/Talla/Color)</label>
              <input formControlName="variante_id" class="form-control" placeholder="UUID de la variante" />
            </div>
            <div class="form-group">
              <label>Cantidad</label>
              <input type="number" formControlName="cantidad" class="form-control" min="1" />
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
    .reservas-page { padding: 24px; font-family: inherit; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .tab-buttons { display: flex; gap: 8px; }
    .btn { padding: 8px 14px; border-radius: 6px; border: 1px solid transparent; cursor: pointer; font-size: 0.88rem; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-outline { border-color: #cbd5e1; background: #fff; }
    .btn-danger { background: #ef4444; color: #fff; }
    .btn-success { background: #10b981; color: #fff; }
    .btn-warning { background: #f59e0b; color: #fff; }
    .btn-sm { padding: 4px 10px; font-size: 0.8rem; }
    .reservas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
    .reserva-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; }
    .card-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
    .codigo { font-weight: 700; color: #1e293b; }
    .badge { padding: 3px 8px; border-radius: 12px; font-size: 0.72rem; text-transform: uppercase; font-weight: 600; }
    .badge-pendiente_preparacion { background: #fef3c7; color: #b45309; }
    .badge-preparada { background: #dcfce7; color: #15803d; }
    .badge-cancelada { background: #f1f5f9; color: #64748b; }
    .badge-incidencia_stock { background: #fee2e2; color: #b91c1c; }
    .card-body p { margin: 4px 0; font-size: 0.85rem; }
    .items-list h5 { margin: 8px 0 4px; font-size: 0.82rem; }
    .items-list ul { margin: 0; padding-left: 18px; font-size: 0.82rem; color: #475569; }
    .ubicacion-tag { background: #e0f2fe; color: #0369a1; padding: 1px 4px; border-radius: 3px; font-size: 0.75rem; }
    .card-actions { display: flex; gap: 8px; margin-top: 14px; border-top: 1px solid #f1f5f9; padding-top: 10px; }
    .alert { padding: 10px; border-radius: 6px; margin-bottom: 16px; font-size: 0.9rem; }
    .alert-error { background: #fee2e2; color: #991b1b; }
    .alert-success { background: #dcfce7; color: #166534; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 420px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.82rem; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class ReservasComponent implements OnInit {
  reservas: Reserva[] = [];
  tab: 'mis' | 'preparar' = 'mis';
  mensajeError = '';
  mensajeExito = '';
  mostrarModalNueva = false;
  reservaForm: FormGroup;

  constructor(
    private readonly reservaService: ReservaService,
    private readonly fb: FormBuilder
  ) {
    this.reservaForm = this.fb.group({
      sucursal_id: ['', Validators.required],
      fecha_visita: ['', Validators.required],
      variante_id: ['', Validators.required],
      cantidad: [1, [Validators.required, Validators.min(1)]],
    });
  }

  ngOnInit(): void {
    this.cargarReservas();
  }

  setTab(nuevaTab: 'mis' | 'preparar'): void {
    this.tab = nuevaTab;
    this.cargarReservas();
  }

  cargarReservas(): void {
    this.mensajeError = '';
    if (this.tab === 'mis') {
      this.reservaService.listarReservas().subscribe({
        next: (resp) => (this.reservas = resp.items),
        error: (err) => (this.mensajeError = err?.error?.detail?.message || 'Error al cargar reservas'),
      });
    } else {
      this.reservaService.listarPorPreparar().subscribe({
        next: (resp) => (this.reservas = resp.items),
        error: (err) => (this.mensajeError = err?.error?.detail?.message || 'Error al cargar reservas por preparar'),
      });
    }
  }

  cancelarReserva(id: string): void {
    if (!confirm('¿Confirma que desea cancelar esta reserva? El stock se liberará de inmediato.')) return;

    this.reservaService.cancelarReserva(id).subscribe({
      next: () => {
        this.mensajeExito = 'Reserva cancelada con éxito';
        this.cargarReservas();
      },
      error: (err) => (this.mensajeError = err?.error?.detail?.message || 'No se pudo cancelar la reserva'),
    });
  }

  prepararReserva(id: string): void {
    const probador = prompt('Ingrese el identificador del probador asignado (ej. Probador 1):') || 'Probador General';
    this.reservaService.prepararReserva(id, probador).subscribe({
      next: () => {
        this.mensajeExito = 'Reserva marcada como preparada. Cliente notificado.';
        this.cargarReservas();
      },
      error: (err) => (this.mensajeError = err?.error?.detail?.message || 'Error al preparar reserva'),
    });
  }

  reportarIncidencia(id: string): void {
    const motivo = prompt('Motivo de la incidencia (prenda dañada, extraviada):');
    if (!motivo) return;

    this.reservaService.reportarIncidencia(id, { variante_ids: [], motivo }).subscribe({
      next: (resp) => {
        this.mensajeExito = 'Incidencia registrada. Se han generado alternativas para el cliente.';
        this.cargarReservas();
      },
      error: (err) => (this.mensajeError = err?.error?.detail?.message || 'Error al reportar incidencia'),
    });
  }

  abrirModalNueva(): void {
    this.mostrarModalNueva = true;
    this.mensajeError = '';
  }

  guardarReserva(): void {
    const val = this.reservaForm.value;
    const idempotencyKey = crypto.randomUUID();

    this.reservaService
      .crearReserva(
        {
          sucursal_id: val.sucursal_id,
          fecha_visita: new Date(val.fecha_visita).toISOString(),
          items: [{ variante_id: val.variante_id, cantidad: Number(val.cantidad) }],
        },
        idempotencyKey
      )
      .subscribe({
        next: (res) => {
          this.mensajeExito = `Reserva creada exitosamente con código digital: ${res.codigo}`;
          this.mostrarModalNueva = false;
          this.cargarReservas();
        },
        error: (err) => {
          this.mensajeError = err?.offline ? err.message : err?.error?.detail?.message || 'Error al reservar prendas';
        },
      });
  }
}

