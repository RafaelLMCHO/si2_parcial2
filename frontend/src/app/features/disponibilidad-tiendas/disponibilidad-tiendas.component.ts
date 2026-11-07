import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { InventarioService } from '../../core/inventario.service';
import { DisponibilidadPrendaResponse } from '../../core/models';

@Component({
  selector: 'app-disponibilidad-tiendas',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="disponibilidad-container">
      <div class="header">
        <h3>Disponibilidad en Tiendas Físicas</h3>
        <span *ngIf="cargando" class="badge loading">Consultando...</span>
      </div>

      <!-- Alerta de Stock Local / Modo Offline (Texto exacto del spec) -->
      <div *ngIf="datos?.es_local" class="alert-offline">
        <strong>⚠️ Stock local:</strong> las existencias mostradas corresponden al último balance descargado y pueden haber variado.
        <small class="fecha-sync" *ngIf="datos?.actualizado_en">
          (Última sincronización: {{ datos?.actualizado_en | date:'short' }})
        </small>
      </div>

      <!-- Alerta Agotado (Flujo alternativo 4.a) -->
      <div *ngIf="datos?.agotado_en_todas" class="alert-agotado">
        <strong>Agotado en todas las tiendas físicas</strong>
      </div>

      <!-- Lista de Sucursales -->
      <div *ngIf="!cargando && datos && !datos.agotado_en_todas" class="sucursales-list">
        <div *ngFor="let suc of datos.sucursales" class="sucursal-card">
          <div class="sucursal-info">
            <span class="sucursal-nombre">{{ suc.nombre }}</span>
            <span class="sucursal-ciudad">📍 {{ suc.ciudad }} - {{ suc.direccion }}</span>
          </div>

          <div class="variantes-chips">
            <div *ngFor="let v of suc.variantes" 
                 class="chip" 
                 [class.chip-disponible]="v.stock_disponible > 0"
                 [class.chip-agotado]="v.stock_disponible <= 0">
              <span class="talla-color">{{ v.talla }} / {{ v.color }}</span>
              <span class="stock-qty">{{ v.stock_disponible }} disp.</span>
            </div>
          </div>
        </div>
      </div>

      <div *ngIf="!cargando && (!datos || datos.sucursales.length === 0) && !datos?.agotado_en_todas" class="empty-state">
        <p>No se encontraron existencias registradas para esta prenda.</p>
      </div>
    </div>
  `,
  styles: [`
    .disponibilidad-container {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px;
      margin-top: 12px;
      font-family: inherit;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .header h3 {
      margin: 0;
      font-size: 1.1rem;
      color: #1e293b;
    }
    .alert-offline {
      background: #fef3c7;
      border-left: 4px solid #f59e0b;
      color: #92400e;
      padding: 10px 14px;
      border-radius: 4px;
      font-size: 0.88rem;
      margin-bottom: 14px;
    }
    .fecha-sync {
      display: block;
      font-size: 0.78rem;
      margin-top: 4px;
      color: #b45309;
    }
    .alert-agotado {
      background: #fee2e2;
      border-left: 4px solid #ef4444;
      color: #991b1b;
      padding: 12px;
      border-radius: 4px;
      text-align: center;
      font-size: 0.95rem;
    }
    .sucursales-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .sucursal-card {
      border: 1px solid #edf2f7;
      border-radius: 6px;
      padding: 12px;
      background: #f8fafc;
    }
    .sucursal-info {
      display: flex;
      flex-direction: column;
      margin-bottom: 8px;
    }
    .sucursal-nombre {
      font-weight: 600;
      color: #0f172a;
    }
    .sucursal-ciudad {
      font-size: 0.82rem;
      color: #64748b;
    }
    .variantes-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.8rem;
      border: 1px solid transparent;
    }
    .chip-disponible {
      background: #ecfdf5;
      border-color: #a7f3d0;
      color: #065f46;
    }
    .chip-agotado {
      background: #f1f5f9;
      border-color: #cbd5e1;
      color: #94a3b8;
    }
    .stock-qty {
      font-weight: bold;
    }
  `]
})
export class DisponibilidadTiendasComponent implements OnInit {
  @Input() prendaId!: string;

  datos: DisponibilidadPrendaResponse | null = null;
  cargando = false;

  constructor(private readonly inventarioService: InventarioService) {}

  ngOnInit(): void {
    if (this.prendaId) {
      this.cargarDisponibilidad();
    }
  }

  cargarDisponibilidad(): void {
    this.cargando = true;
    this.inventarioService.consultarDisponibilidad(this.prendaId).subscribe({
      next: (resp) => {
        this.datos = resp;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }
}

