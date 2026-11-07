import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { InventarioService } from '../../core/inventario.service';
import { InventarioPrenda } from '../../core/models';

@Component({
  selector: 'app-inventario',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="inventario-page">
      <div class="header-actions">
        <h2>Gestión de Inventarios y Existencias</h2>
        <div class="btn-group">
          <button class="btn btn-primary" (click)="abrirModal('ingreso')">+ Ingreso por Lote</button>
          <button class="btn btn-warning" (click)="abrirModal('ajuste')">⚙ Ajuste / Merma</button>
          <button class="btn btn-secondary" (click)="abrirModal('transferencia')">⇄ Transferencia</button>
          <button class="btn btn-outline" (click)="toggleKardex()">
            {{ verKardex ? 'Ver Matriz' : 'Ver Kárdex' }}
          </button>
        </div>
      </div>

      <!-- Filtros -->
      <div class="filters-bar" *ngIf="!verKardex">
        <input type="text" placeholder="Buscar por SKU o Nombre..." [(ngModel)]="busqueda" (input)="cargarInventario()" class="input-search" />
        <label class="checkbox-label">
          <input type="checkbox" [(ngModel)]="soloBajoMinimo" (change)="cargarInventario()" />
          Solo existencias bajo mínimo
        </label>
      </div>

      <!-- Mensajes de Error de Negocio / Aislamiento -->
      <div *ngIf="errorMensaje" class="alert alert-error">
        {{ errorMensaje }}
      </div>
      <div *ngIf="exitoMensaje" class="alert alert-success">
        {{ exitoMensaje }}
      </div>

      <!-- Tabla Matriz de Existencias (CU-17) -->
      <div class="table-container" *ngIf="!verKardex">
        <table class="data-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Prenda</th>
              <th>Talla / Color</th>
              <th>P. Venta</th>
              <th>Sucursal</th>
              <th>Físico</th>
              <th>Reservado</th>
              <th>Disponible</th>
              <th>Mínimo</th>
              <th>Ubicación</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <ng-container *ngFor="let item of items">
              <tr *ngFor="let ex of item.existencias">
                <td><code>{{ item.sku }}</code></td>
                <td>{{ item.prenda_nombre }}</td>
                <td>{{ item.talla }} / {{ item.color }}</td>
                <td>{{ item.precio_venta | currency:'BOB ':'symbol':'1.2-2' }}</td>
                <td>{{ ex.sucursal_nombre }}</td>
                <td>{{ ex.stock_fisico }}</td>
                <td>{{ ex.stock_reservado }}</td>
                <td><strong>{{ ex.stock_disponible }}</strong></td>
                <td>{{ ex.stock_minimo }}</td>
                <td>{{ ex.ubicacion || 'Sin asignar' }}</td>
                <td>
                  <span class="badge" [class.badge-danger]="ex.bajo_minimo" [class.badge-success]="!ex.bajo_minimo">
                    {{ ex.bajo_minimo ? 'Bajo Mínimo' : 'Normal' }}
                  </span>
                </td>
              </tr>
            </ng-container>
            <tr *ngIf="items.length === 0">
              <td colspan="11" class="text-center">No hay registros de inventario.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Vista de Kárdex Inmutable -->
      <div class="table-container" *ngIf="verKardex">
        <h3>Historial Kárdex de Movimientos</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Fecha/Hora</th>
              <th>Tipo</th>
              <th>Cantidad</th>
              <th>Stock Anterior</th>
              <th>Stock Nuevo</th>
              <th>Motivo</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let m of movimientos">
              <td>{{ m.ocurrido_en | date:'short' }}</td>
              <td><span class="badge-tipo">{{ m.tipo }}</span></td>
              <td [class.text-danger]="m.cantidad < 0" [class.text-success]="m.cantidad > 0">
                {{ m.cantidad > 0 ? '+' + m.cantidad : m.cantidad }}
              </td>
              <td>{{ m.stock_anterior }}</td>
              <td><strong>{{ m.stock_nuevo }}</strong></td>
              <td>{{ m.motivo || 'Operación regular' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal Registrar Movimiento (Ingreso / Ajuste / Transferencia) -->
      <div class="modal-backdrop" *ngIf="modalTipo">
        <div class="modal-card">
          <h3>
            <span *ngIf="modalTipo === 'ingreso'">Ingreso de Prendas por Lote</span>
            <span *ngIf="modalTipo === 'ajuste'">Ajuste de Stock / Merma</span>
            <span *ngIf="modalTipo === 'transferencia'">Transferencia entre Sucursales</span>
          </h3>

          <form [formGroup]="movimientoForm" (ngSubmit)="guardarMovimiento()">
            <!-- Sucursal Origen -->
            <div class="form-group">
              <label>Sucursal {{ modalTipo === 'transferencia' ? 'Origen' : '' }}</label>
              <input formControlName="sucursal_id" class="form-control" placeholder="UUID de Sucursal" />
            </div>

            <!-- Sucursal Destino (solo transferencia) -->
            <div class="form-group" *ngIf="modalTipo === 'transferencia'">
              <label>Sucursal Destino</label>
              <input formControlName="destino_id" class="form-control" placeholder="UUID Sucursal Destino" />
            </div>

            <!-- Variante ID -->
            <div class="form-group">
              <label>Variante (SKU)</label>
              <input formControlName="variante_id" class="form-control" placeholder="UUID de Variante" />
            </div>

            <!-- Cantidad -->
            <div class="form-group">
              <label>Cantidad {{ modalTipo === 'ajuste' ? '(Negativo para merma)' : '' }}</label>
              <input type="number" formControlName="cantidad" class="form-control" />
            </div>

            <!-- Motivo -->
            <div class="form-group">
              <label>Motivo</label>
              <input formControlName="motivo" class="form-control" placeholder="Razón del movimiento" />
            </div>

            <div class="modal-actions">
              <button type="button" class="btn btn-outline" (click)="cerrarModal()">Cancelar</button>
              <button type="submit" class="btn btn-primary" [disabled]="movimientoForm.invalid">Procesar</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .inventario-page { padding: 24px; font-family: inherit; }
    .header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn-group { display: flex; gap: 8px; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: 500; font-size: 0.9rem; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-warning { background: #f59e0b; color: #fff; }
    .btn-secondary { background: #4b5563; color: #fff; }
    .btn-outline { background: transparent; border: 1px solid #cbd5e1; color: #334155; }
    .filters-bar { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
    .input-search { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; width: 300px; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
    .badge { padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-tipo { background: #e0e7ff; color: #3730a3; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; }
    .alert { padding: 12px; border-radius: 6px; margin-bottom: 16px; }
    .alert-error { background: #fee2e2; color: #991b1b; border-left: 4px solid #ef4444; }
    .alert-success { background: #dcfce7; color: #166534; border-left: 4px solid #22c55e; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 440px; }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
    .text-danger { color: #dc2626; }
    .text-success { color: #16a34a; }
  `]
})
export class InventarioComponent implements OnInit {
  items: InventarioPrenda[] = [];
  movimientos: any[] = [];
  busqueda = '';
  soloBajoMinimo = false;
  verKardex = false;
  modalTipo: 'ingreso' | 'ajuste' | 'transferencia' | null = null;
  errorMensaje = '';
  exitoMensaje = '';
  movimientoForm: FormGroup;

  constructor(
    private readonly inventarioService: InventarioService,
    private readonly fb: FormBuilder
  ) {
    this.movimientoForm = this.fb.group({
      sucursal_id: ['', Validators.required],
      destino_id: [''],
      variante_id: ['', Validators.required],
      cantidad: [1, [Validators.required]],
      motivo: ['', Validators.required],
    });
  }

  ngOnInit(): void {
    this.cargarInventario();
  }

  cargarInventario(): void {
    this.inventarioService
      .listarInventario({
        q: this.busqueda || undefined,
        solo_bajo_minimo: this.soloBajoMinimo,
      })
      .subscribe({
        next: (resp) => {
          this.items = resp.items;
        },
        error: (err) => {
          this.errorMensaje = err?.error?.detail?.message || 'Error al cargar inventario';
        },
      });
  }

  toggleKardex(): void {
    this.verKardex = !this.verKardex;
    if (this.verKardex) {
      this.inventarioService.listarMovimientos().subscribe({
        next: (resp) => (this.movimientos = resp.items || []),
      });
    }
  }

  abrirModal(tipo: 'ingreso' | 'ajuste' | 'transferencia'): void {
    this.modalTipo = tipo;
    this.errorMensaje = '';
    this.exitoMensaje = '';
    this.movimientoForm.reset({ cantidad: tipo === 'ajuste' ? -1 : 1 });
  }

  cerrarModal(): void {
    this.modalTipo = null;
  }

  guardarMovimiento(): void {
    const val = this.movimientoForm.value;
    if (this.modalTipo === 'ingreso') {
      this.inventarioService
        .registrarIngreso({
          sucursal_id: val.sucursal_id,
          items: [{ variante_id: val.variante_id, cantidad: Number(val.cantidad) }],
          motivo: val.motivo,
        })
        .subscribe({
          next: () => this.manejarExito('Ingreso registrado con éxito'),
          error: (err) => this.manejarError(err),
        });
    } else if (this.modalTipo === 'ajuste') {
      this.inventarioService
        .registrarAjuste({
          sucursal_id: val.sucursal_id,
          variante_id: val.variante_id,
          cantidad: Number(val.cantidad),
          motivo: val.motivo,
        })
        .subscribe({
          next: () => this.manejarExito('Ajuste procesado con éxito'),
          error: (err) => this.manejarError(err),
        });
    } else if (this.modalTipo === 'transferencia') {
      this.inventarioService
        .crearTransferencia({
          origen_id: val.sucursal_id,
          destino_id: val.destino_id,
          items: [{ variante_id: val.variante_id, cantidad: Number(val.cantidad) }],
          motivo: val.motivo,
        })
        .subscribe({
          next: () => this.manejarExito('Transferencia realizada con éxito'),
          error: (err) => this.manejarError(err),
        });
    }
  }

  private manejarExito(msg: string): void {
    this.exitoMensaje = msg;
    this.cerrarModal();
    this.cargarInventario();
  }

  private manejarError(err: any): void {
    if (err?.status === 409) {
      this.errorMensaje = `Conflicto de stock: ${err.error?.detail?.message || 'Stock insuficiente'}`;
    } else if (err?.status === 403) {
      this.errorMensaje = `Aislamiento de Empresa: Operación bloqueada (403)`;
    } else {
      this.errorMensaje = err?.error?.detail?.message || 'Error en la operación';
    }
  }
}

