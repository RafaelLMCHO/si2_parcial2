import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PosService } from '../../core/pos.service';

interface PosLinea {
  variante_id: string;
  sku: string;
  prenda_nombre: string;
  talla: string;
  color: string;
  precio_unitario: number;
  cantidad: number;
  subtotal: number;
}

@Component({
  selector: 'app-pos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="pos-layout">
      <!-- Panel Izquierdo: Artículos y Búsqueda -->
      <div class="pos-main">
        <div class="scanner-header">
          <input #scannerInput 
                 type="text" 
                 class="scanner-box" 
                 placeholder="Escanear código de barras o ingresar SKU..." 
                 [(ngModel)]="codigoEscaneado" 
                 (keyup.enter)="escanearArticulo()" />
          <button class="btn btn-secondary" (click)="escanearArticulo()">Agregar</button>
        </div>

        <div *ngIf="mensajeError" class="alert alert-error">{{ mensajeError }}</div>

        <div class="ticket-table-container">
          <table class="ticket-table">
            <thead>
              <tr>
                <th>Artículo</th>
                <th>Talla/Color</th>
                <th>Precio</th>
                <th>Cant.</th>
                <th>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let it of lineas; let i = index">
                <td><strong>{{ it.prenda_nombre }}</strong><br><small>{{ it.sku }}</small></td>
                <td>{{ it.talla }} / {{ it.color }}</td>
                <td>{{ it.precio_unitario | currency:'BOB ':'symbol':'1.2-2' }}</td>
                <td>
                  <input type="number" [(ngModel)]="it.cantidad" min="1" (change)="recalcularLineas()" class="qty-control" />
                </td>
                <td><strong>{{ it.subtotal | currency:'BOB ':'symbol':'1.2-2' }}</strong></td>
                <td>
                  <button class="btn-del" (click)="quitarLinea(i)">✕</button>
                </td>
              </tr>
              <tr *ngIf="lineas.length === 0">
                <td colspan="6" class="empty-hint">Escanee o busque prendas para comenzar la venta.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Panel Derecho: Cobro y Facturación -->
      <div class="pos-sidebar">
        <div class="totales-display">
          <span class="total-label">TOTAL A PAGAR</span>
          <span class="total-monto">{{ totalAPagar | currency:'BOB ':'symbol':'1.2-2' }}</span>
        </div>

        <!-- Datos de Facturación (CU-23) -->
        <div class="section-box">
          <h4>Datos de Facturación</h4>
          <div class="radio-row">
            <label><input type="radio" value="consumidor_final" [(ngModel)]="tipoCliente" /> Consumidor Final</label>
            <label><input type="radio" value="identificado" [(ngModel)]="tipoCliente" /> Con Factura</label>
          </div>
          <div *ngIf="tipoCliente === 'identificado'" class="form-grid">
            <input type="text" placeholder="Razón Social / Nombre" [(ngModel)]="clienteNombre" class="form-input" />
            <input type="text" placeholder="NIT / CI" [(ngModel)]="clienteDocumento" class="form-input" />
          </div>
        </div>

        <!-- Forma de Pago -->
        <div class="section-box">
          <h4>Forma de Pago</h4>
          <div class="metodo-chips">
            <button class="chip-btn" [class.active]="metodoPago === 'efectivo'" (click)="metodoPago = 'efectivo'">💵 Efectivo</button>
            <button class="chip-btn" [class.active]="metodoPago === 'tarjeta'" (click)="metodoPago = 'tarjeta'">💳 Tarjeta</button>
            <button class="chip-btn" [class.active]="metodoPago === 'qr'" (click)="metodoPago = 'qr'">📱 QR</button>
          </div>

          <!-- Efectivo con cálculo de cambio en vivo -->
          <div *ngIf="metodoPago === 'efectivo'" class="efectivo-box">
            <label>Monto Recibido:</label>
            <input type="number" [(ngModel)]="montoRecibido" (input)="calcularCambio()" class="form-input monto-input" />
            <div class="cambio-display" [class.negativo]="cambio < 0">
              <span>{{ cambio >= 0 ? 'Cambio a devolver:' : 'Saldo insuficiente (falta):' }}</span>
              <strong>{{ (cambio >= 0 ? cambio : -cambio) | currency:'BOB ':'symbol':'1.2-2' }}</strong>
            </div>
          </div>

          <!-- QR -->
          <div *ngIf="metodoPago === 'qr'" class="qr-box">
            <input type="text" placeholder="Código / N° de Referencia Bancaria" [(ngModel)]="referenciaPago" class="form-input" />
          </div>
        </div>

        <button class="btn btn-primary btn-cobrar" 
                (click)="cobrarVenta()" 
                [disabled]="lineas.length === 0 || (metodoPago === 'efectivo' && cambio < 0)">
          FINALIZAR Y COBRAR (F12)
        </button>
      </div>

      <!-- Modal de Ticket / Impresión -->
      <div class="modal-backdrop" *ngIf="ticketImprimir">
        <div class="modal-ticket">
          <h3>Comprobante de Venta</h3>
          <pre class="ticket-preview">{{ ticketImprimir | json }}</pre>
          <div class="modal-actions">
            <button class="btn btn-secondary" (click)="imprimirTicket()">Imprimir Ticket (80 mm)</button>
            <button class="btn btn-outline" (click)="ticketImprimir = null; reiniciarVenta()">Nueva Venta</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .pos-layout { display: flex; height: calc(100vh - 80px); gap: 16px; padding: 16px; font-family: inherit; box-sizing: border-box; }
    .pos-main { flex: 1; display: flex; flex-direction: column; background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 16px; }
    .scanner-header { display: flex; gap: 8px; margin-bottom: 14px; }
    .scanner-box { flex: 1; font-size: 1.1rem; padding: 10px 14px; border: 2px solid #2563eb; border-radius: 6px; outline: none; }
    .ticket-table-container { flex: 1; overflow-y: auto; }
    .ticket-table { width: 100%; border-collapse: collapse; }
    .ticket-table th { background: #f8fafc; padding: 8px 12px; font-size: 0.82rem; text-align: left; }
    .ticket-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 0.88rem; }
    .qty-control { width: 55px; padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px; }
    .btn-del { background: transparent; border: none; color: #ef4444; font-weight: bold; cursor: pointer; }
    .empty-hint { text-align: center; color: #94a3b8; padding: 40px; }
    .pos-sidebar { width: 380px; display: flex; flex-direction: column; gap: 14px; }
    .totales-display { background: #0f172a; color: #fff; padding: 20px; border-radius: 8px; text-align: right; }
    .total-label { display: block; font-size: 0.85rem; color: #94a3b8; letter-spacing: 1px; }
    .total-monto { font-size: 2.2rem; font-weight: 700; color: #38bdf8; }
    .section-box { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; }
    .section-box h4 { margin: 0 0 10px 0; font-size: 0.9rem; color: #334155; }
    .radio-row { display: flex; gap: 14px; margin-bottom: 8px; font-size: 0.85rem; }
    .form-grid { display: flex; flex-direction: column; gap: 6px; }
    .form-input { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.88rem; width: 100%; box-sizing: border-box; }
    .metodo-chips { display: flex; gap: 8px; }
    .chip-btn { flex: 1; padding: 8px; border: 1px solid #cbd5e1; background: #fff; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
    .chip-btn.active { background: #2563eb; color: #fff; border-color: #2563eb; font-weight: 600; }
    .efectivo-box { margin-top: 10px; }
    .monto-input { font-size: 1.1rem; font-weight: bold; }
    .cambio-display { display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.9rem; padding: 8px; background: #f0fdf4; border-radius: 4px; color: #166534; }
    .cambio-display.negativo { background: #fef2f2; color: #991b1b; }
    .btn-cobrar { width: 100%; padding: 16px; font-size: 1.1rem; font-weight: 700; border-radius: 8px; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }
    .btn-primary { background: #16a34a; color: #fff; }
    .btn-secondary { background: #475569; color: #fff; }
    .btn-outline { background: #fff; border: 1px solid #cbd5e1; }
    .alert-error { background: #fee2e2; color: #991b1b; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; font-size: 0.85rem; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; }
    .modal-ticket { background: #fff; padding: 24px; border-radius: 8px; width: 420px; max-height: 80vh; overflow-y: auto; }
    .ticket-preview { background: #f8fafc; padding: 12px; font-size: 0.78rem; border-radius: 4px; max-height: 250px; overflow-y: auto; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class PosComponent implements OnInit {
  @ViewChild('scannerInput') scannerInput!: ElementRef<HTMLInputElement>;

  codigoEscaneado = '';
  lineas: PosLinea[] = [];
  tipoCliente: 'consumidor_final' | 'identificado' = 'consumidor_final';
  clienteNombre = '';
  clienteDocumento = '';
  metodoPago: 'efectivo' | 'tarjeta' | 'qr' = 'efectivo';
  montoRecibido = 0;
  cambio = 0;
  totalAPagar = 0;
  referenciaPago = '';
  mensajeError = '';
  ticketImprimir: any = null;

  constructor(private readonly posService: PosService) {}

  ngOnInit(): void {
    setTimeout(() => this.scannerInput?.nativeElement?.focus(), 300);
  }

  escanearArticulo(): void {
    if (!this.codigoEscaneado.trim()) return;
    this.mensajeError = '';

    this.posService.buscarPorBarcode(this.codigoEscaneado.trim()).subscribe({
      next: (art) => {
        const existente = this.lineas.find((l) => l.variante_id === art.variante_id);
        if (existente) {
          existente.cantidad += 1;
        } else {
          this.lineas.push({
            variante_id: art.variante_id,
            sku: art.sku,
            prenda_nombre: art.prenda_nombre,
            talla: art.talla,
            color: art.color,
            precio_unitario: Number(art.precio_venta),
            cantidad: 1,
            subtotal: Number(art.precio_venta),
          });
        }
        this.codigoEscaneado = '';
        this.recalcularLineas();
        this.scannerInput?.nativeElement?.focus();
      },
      error: (err) => {
        this.mensajeError = err?.error?.detail?.message || 'Artículo no encontrado en la sucursal';
      },
    });
  }

  recalcularLineas(): void {
    let subtotal = 0;
    this.lineas.forEach((l) => {
      l.subtotal = l.precio_unitario * l.cantidad;
      subtotal += l.subtotal;
    });
    // IVA 13% incluido
    this.totalAPagar = subtotal * 1.13;
    this.calcularCambio();
  }

  calcularCambio(): void {
    if (this.metodoPago === 'efectivo') {
      this.cambio = (this.montoRecibido || 0) - this.totalAPagar;
    } else {
      this.cambio = 0;
    }
  }

  quitarLinea(index: number): void {
    this.lineas.splice(index, 1);
    this.recalcularLineas();
  }

  cobrarVenta(): void {
    this.mensajeError = '';
    const idempotencyKey = crypto.randomUUID();

    const payload = {
      idempotency_key: idempotencyKey,
      items: this.lineas.map((l) => ({
        variante_id: l.variante_id,
        cantidad: l.cantidad,
      })),
      cliente: {
        tipo: this.tipoCliente,
        nombre: this.tipoCliente === 'identificado' ? this.clienteNombre : undefined,
        documento: this.tipoCliente === 'identificado' ? this.clienteDocumento : undefined,
      },
      pago: {
        metodo: this.metodoPago,
        monto_recibido: this.metodoPago === 'efectivo' ? this.montoRecibido : undefined,
        referencia: this.metodoPago === 'qr' ? this.referenciaPago : undefined,
      },
    };

    this.posService.registrarVenta(payload).subscribe({
      next: (resp) => {
        this.posService.imprimirTicket(resp.venta_id).subscribe({
          next: (ticketData) => {
            this.ticketImprimir = ticketData;
          },
        });
      },
      error: (err) => {
        this.mensajeError = err?.message || err?.error?.detail?.message || 'Error al procesar cobro en mostrador';
      },
    });
  }

  imprimirTicket(): void {
    window.print();
  }

  reiniciarVenta(): void {
    this.lineas = [];
    this.totalAPagar = 0;
    this.montoRecibido = 0;
    this.cambio = 0;
    this.ticketImprimir = null;
    this.scannerInput?.nativeElement?.focus();
  }
}

