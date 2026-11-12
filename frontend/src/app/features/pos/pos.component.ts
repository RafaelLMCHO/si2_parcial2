import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { of, switchMap, throwError } from 'rxjs';
import { apiErrorMessage } from '../../core/error-mapper';
import { PagoService } from '../../core/pago.service';
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
    <div class="pos-container">
      <!-- PANEL IZQUIERDO: SCANNER, CATÁLOGO RÁPIDO Y TICKET DE VENTA -->
      <section class="pos-left-panel">
        <!-- BARRA SUPERIOR DE ENTRADA / SCANNER -->
        <div class="scanner-card">
          <div class="scanner-input-group">
            <span class="scanner-icon">🏷️</span>
            <input
              #scannerInput
              type="text"
              class="scanner-input"
              placeholder="Escanear código de barras o ingresar SKU (Enter)..."
              [(ngModel)]="codigoEscaneado"
              (keyup.enter)="escanearArticulo()"
              autofocus
            />
            <button
              type="button"
              class="btn-scanner-add"
              (click)="escanearArticulo()"
              [disabled]="!codigoEscaneado.trim()"
            >
              <span>+</span> Agregar
            </button>
          </div>

          @if (mensajeError) {
            <div class="alert-banner error animate-shake">
              <span class="alert-icon">⚠️</span>
              <span class="alert-text">{{ mensajeError }}</span>
              <button type="button" class="alert-close" (click)="mensajeError = ''">✕</button>
            </div>
          }
        </div>

        <!-- TABLA DE ARTÍCULOS EN CAJA -->
        <div class="cart-table-card">
          <div class="table-header-info">
            <h3 class="table-title">Detalle de la Orden</h3>
            <span class="items-badge">{{ lineas.length }} {{ lineas.length === 1 ? 'artículo' : 'artículos' }}</span>
          </div>

          <div class="table-responsive">
            <table class="pos-table">
              <thead>
                <tr>
                  <th style="width: 40%">Artículo & Variante</th>
                  <th style="width: 18%" class="text-right">Precio Unit.</th>
                  <th style="width: 22%" class="text-center">Cantidad</th>
                  <th style="width: 15%" class="text-right">Subtotal</th>
                  <th style="width: 5%" class="text-center"></th>
                </tr>
              </thead>
              <tbody>
                @for (it of lineas; track it.variante_id; let i = $index) {
                  <tr class="item-row">
                    <td>
                      <div class="item-name">{{ it.prenda_nombre }}</div>
                      <div class="item-meta">
                        <span class="meta-tag">{{ it.talla }}</span>
                        <span class="meta-tag">{{ it.color }}</span>
                        <span class="meta-sku">{{ it.sku }}</span>
                      </div>
                    </td>
                    <td class="text-right num-font">
                      BOB {{ it.precio_unitario | number:'1.2-2' }}
                    </td>
                    <td class="text-center">
                      <div class="qty-stepper">
                        <button type="button" class="btn-qty" (click)="decrementarCantidad(i)">−</button>
                        <span class="qty-val">{{ it.cantidad }}</span>
                        <button type="button" class="btn-qty" (click)="incrementarCantidad(i)">+</button>
                      </div>
                    </td>
                    <td class="text-right num-font font-bold">
                      BOB {{ it.subtotal | number:'1.2-2' }}
                    </td>
                    <td class="text-center">
                      <button
                        type="button"
                        class="btn-row-del"
                        (click)="quitarLinea(i)"
                        title="Quitar artículo"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                }

                @if (lineas.length === 0) {
                  <tr>
                    <td colspan="5" class="empty-state">
                      <div class="empty-illustration">🛒</div>
                      <div class="empty-title">Caja lista para nueva venta</div>
                      <div class="empty-desc">Escanee códigos con la pistola lectora o digite el SKU de la prenda para iniciar.</div>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>

          <!-- RESUMEN EN PIE DE TABLA -->
          <div class="table-footer-summary">
            <button
              type="button"
              class="btn-reset-order"
              (click)="reiniciarVenta()"
              [disabled]="lineas.length === 0"
            >
              Cancelar Orden
            </button>
            <div class="subtotal-indicator">
              <span>Subtotal Neto:</span>
              <strong>BOB {{ subtotalNeto | number:'1.2-2' }}</strong>
            </div>
          </div>
        </div>
      </section>

      <!-- PANEL DERECHO: TERMINAL DE COBRO Y FACTURACIÓN -->
      <aside class="pos-right-panel">
        <!-- DISPLAY PRINCIPAL DE TOTAL (ESTILO LED / DARK SLATE) -->
        <div class="total-display-card">
          <div class="total-header">
            <span class="total-title">TOTAL A COBRAR</span>
            <span class="iva-pill">IVA 13% Incluido</span>
          </div>
          <div class="total-amount-row">
            <span class="currency-symbol">BOB</span>
            <span class="total-number">{{ totalAPagar | number:'1.2-2' }}</span>
          </div>
        </div>

        <!-- DATOS DE FACTURACIÓN (CU-23) -->
        <div class="checkout-card">
          <div class="card-title-row">
            <span class="card-icon">📑</span>
            <h4>Facturación</h4>
          </div>

          <div class="client-type-tabs">
            <button
              type="button"
              class="tab-btn"
              [class.active]="tipoCliente === 'consumidor_final'"
              (click)="tipoCliente = 'consumidor_final'"
            >
              Consumidor Final
            </button>
            <button
              type="button"
              class="tab-btn"
              [class.active]="tipoCliente === 'identificado'"
              (click)="tipoCliente = 'identificado'"
            >
              Con Factura (NIT)
            </button>
          </div>

          @if (tipoCliente === 'identificado') {
            <div class="client-form-grid animate-fade-in">
              <input
                type="text"
                placeholder="Razón Social o Nombre Completo"
                [(ngModel)]="clienteNombre"
                class="pos-input"
              />
              <input
                type="text"
                placeholder="NIT / Cédula de Identidad (CI)"
                [(ngModel)]="clienteDocumento"
                class="pos-input"
              />
            </div>
          }
        </div>

        <!-- SECCIÓN DE MÉTODO DE PAGO -->
        <div class="checkout-card">
          <div class="card-title-row">
            <span class="card-icon">💳</span>
            <h4>Método de Pago</h4>
          </div>

          <div class="payment-methods-grid">
            <button
              type="button"
              class="payment-tile"
              [class.selected]="metodoPago === 'efectivo'"
              (click)="metodoPago = 'efectivo'"
            >
              <span class="tile-icon">💵</span>
              <span class="tile-label">Efectivo</span>
            </button>
            <button
              type="button"
              class="payment-tile"
              [class.selected]="metodoPago === 'tarjeta'"
              (click)="metodoPago = 'tarjeta'"
            >
              <span class="tile-icon">💳</span>
              <span class="tile-label">Tarjeta POS</span>
            </button>
            <button
              type="button"
              class="payment-tile"
              [class.selected]="metodoPago === 'qr'"
              (click)="metodoPago = 'qr'"
            >
              <span class="tile-icon">📱</span>
              <span class="tile-label">QR Simple</span>
            </button>
          </div>

          <!-- DETALLE EFECTIVO: BOTONES RÁPIDOS Y CÁLCULO DE CAMBIO -->
          @if (metodoPago === 'efectivo') {
            <div class="cash-calculator animate-fade-in">
              <label class="input-label">Monto Recibido:</label>
              <div class="cash-input-box">
                <span class="prefix">BOB</span>
                <input
                  type="number"
                  [(ngModel)]="montoRecibido"
                  (input)="calcularCambio()"
                  class="cash-input"
                  min="0"
                  step="1"
                />
              </div>

              <!-- BOTONES RÁPIDOS DE BILLETES BOLIVIANOS -->
              <div class="quick-cash-row">
                <button type="button" class="btn-quick-cash" (click)="setMontoExacto()">Exacto</button>
                <button type="button" class="btn-quick-cash" (click)="sumarEfectivo(20)">+20</button>
                <button type="button" class="btn-quick-cash" (click)="sumarEfectivo(50)">+50</button>
                <button type="button" class="btn-quick-cash" (click)="sumarEfectivo(100)">+100</button>
                <button type="button" class="btn-quick-cash" (click)="sumarEfectivo(200)">+200</button>
              </div>

              <!-- INDICADOR DE CAMBIO -->
              <div class="change-card" [class.negative]="cambio < 0">
                <span class="change-label">
                  {{ cambio >= 0 ? 'Cambio a Devolver:' : 'Falta por Pagar:' }}
                </span>
                <span class="change-amount">
                  BOB {{ (cambio >= 0 ? cambio : -cambio) | number:'1.2-2' }}
                </span>
              </div>
            </div>
          }

          <!-- DETALLE QR -->
          @if (metodoPago === 'qr') {
            <div class="qr-payment-box animate-fade-in">
              <input
                type="text"
                placeholder="N° de Referencia de Pago / Transacción"
                [(ngModel)]="referenciaPago"
                class="pos-input"
              />
            </div>
          }
        </div>

        <!-- BOTÓN PRINCIPAL DE COBRAR -->
        <button
          type="button"
          class="btn-charge-main"
          (click)="cobrarVenta()"
          [disabled]="lineas.length === 0 || procesandoCobro || (metodoPago === 'efectivo' && cambio < 0)"
        >
          <span class="charge-icon">⚡</span>
          <span class="charge-label">{{ procesandoCobro ? 'PROCESANDO COBRO...' : 'FINALIZAR Y COBRAR (F12)' }}</span>
        </button>
      </aside>

      <!-- MODAL TICKET TÉRMICO FORMATEADO (80mm REALISTA) -->
      @if (ticketImprimir) {
        <div class="ticket-modal-overlay">
          <div class="ticket-modal-card">
            <div class="thermal-receipt">
              <!-- ENCABEZADO TÉRMICO -->
              <div class="receipt-header">
                <h2 class="receipt-brand">{{ ticketImprimir.empresa_nombre || 'FASHION STORE S.A.' }}</h2>
                <div class="receipt-sub">CASA MATRIZ - SUCURSAL {{ ticketImprimir.sucursal_nombre || 'CENTRAL' }}</div>
                <div class="receipt-sub">{{ ticketImprimir.sucursal_direccion || 'Av. San Martín #450, Santa Cruz' }}</div>
                <div class="receipt-sub">NIT: {{ ticketImprimir.empresa_nit || '1029384756' }}</div>
                <div class="receipt-divider">================================</div>
                <div class="receipt-title">FACTURA / TICKET POS</div>
                <div class="receipt-number">N° {{ ticketImprimir.numero || 'T-00492' }}</div>
                <div class="receipt-date">{{ ticketImprimir.fecha_hora | date:'dd/MM/yyyy HH:mm:ss' }}</div>
                <div class="receipt-divider">--------------------------------</div>
              </div>

              <!-- DATOS CLIENTE -->
              <div class="receipt-client">
                <div><strong>CLIENTE:</strong> {{ ticketImprimir.cliente_nombre || 'CONSUMIDOR FINAL' }}</div>
                <div><strong>NIT/CI:</strong> {{ ticketImprimir.cliente_documento || '0' }}</div>
                <div class="receipt-divider">--------------------------------</div>
              </div>

              <!-- LÍNEAS DE PRODUCTOS -->
              <div class="receipt-items">
                <div class="item-head">
                  <span>CANT. ARTÍCULO</span>
                  <span>SUBTOTAL</span>
                </div>
                @for (it of lineas; track it.variante_id) {
                  <div class="receipt-item-line">
                    <div class="it-desc">{{ it.cantidad }}x {{ it.prenda_nombre }} ({{ it.talla }}/{{ it.color }})</div>
                    <div class="it-price">BOB {{ it.subtotal | number:'1.2-2' }}</div>
                  </div>
                }
                <div class="receipt-divider">--------------------------------</div>
              </div>

              <!-- TOTALES -->
              <div class="receipt-totals">
                <div class="tot-row">
                  <span>SUBTOTAL:</span>
                  <span>BOB {{ subtotalNeto | number:'1.2-2' }}</span>
                </div>
                <div class="tot-row">
                  <span>IVA INCLUIDO (13%):</span>
                  <span>BOB {{ (totalAPagar - subtotalNeto) | number:'1.2-2' }}</span>
                </div>
                <div class="tot-row main-total">
                  <span>TOTAL A PAGAR:</span>
                  <span>BOB {{ totalAPagar | number:'1.2-2' }}</span>
                </div>
                <div class="tot-row">
                  <span>PAGO ({{ metodoPago | uppercase }}):</span>
                  <span>BOB {{ (metodoPago === 'efectivo' ? montoRecibido : totalAPagar) | number:'1.2-2' }}</span>
                </div>
                @if (metodoPago === 'efectivo') {
                  <div class="tot-row">
                    <span>CAMBIO ENTREGADO:</span>
                    <span>BOB {{ cambio | number:'1.2-2' }}</span>
                  </div>
                }
                <div class="receipt-divider">================================</div>
              </div>

              <!-- PIE Y CÓDIGO QR -->
              <div class="receipt-footer">
                <div class="qr-placeholder">
                  <div class="qr-mock">
                    <span class="qr-symbol">▦</span>
                  </div>
                  <div class="qr-hash">FIRMA DIGITAL: {{ ticketImprimir.firma_qr?.slice(0, 24) || 'FS-BOL-2026-X99Q2B' }}...</div>
                </div>
                <p class="tributary-legend">
                  "ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY"
                </p>
                <div class="gracias-msg">¡GRACIAS POR SU COMPRA!</div>
              </div>
            </div>

            <!-- BOTONES DE ACCIÓN DEL MODAL -->
            <div class="modal-buttons-row">
              <button type="button" class="btn-print" (click)="imprimirTicket()">
                🖨️ Imprimir Ticket (80mm)
              </button>
              <button type="button" class="btn-new-sale" (click)="ticketImprimir = null; reiniciarVenta()">
                ✨ Nueva Venta
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .pos-container {
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 1.5rem;
      min-height: calc(100vh - 120px);
      font-family: inherit;
    }

    /* ------------------------------------------------------------------------
       PANEL IZQUIERDO: SCANNER Y TABLA
       ------------------------------------------------------------------------ */
    .pos-left-panel {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .scanner-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1rem 1.25rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .scanner-input-group {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .scanner-icon {
      font-size: 1.4rem;
    }

    .scanner-input {
      flex: 1;
      height: 48px;
      border: 2px solid #cbd5e1;
      border-radius: 10px;
      padding: 0 1rem;
      font-size: 1.05rem;
      font-weight: 500;
      color: #0f172a;
      outline: none;
      transition: all 0.2s ease;
    }

    .scanner-input:focus {
      border-color: #be185d;
      box-shadow: 0 0 0 4px rgba(190, 24, 93, 0.12);
    }

    .btn-scanner-add {
      height: 48px;
      padding: 0 1.5rem;
      border: 0;
      border-radius: 10px;
      background: #be185d;
      color: #ffffff;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: background 0.2s ease;
    }

    .btn-scanner-add:hover:not(:disabled) {
      background: #9d174d;
    }

    .btn-scanner-add:disabled {
      background: #e2e8f0;
      color: #94a3b8;
      cursor: not-allowed;
    }

    .alert-banner {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      margin-top: 0.75rem;
      padding: 0.65rem 1rem;
      border-radius: 8px;
      font-size: 0.88rem;
    }

    .alert-banner.error {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #b91c1c;
    }

    .alert-text {
      flex: 1;
    }

    .alert-close {
      background: transparent;
      border: 0;
      color: #b91c1c;
      font-size: 1rem;
      cursor: pointer;
    }

    /* Tabla de Artículos */
    .cart-table-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      flex: 1;
      display: flex;
      flex-direction: column;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      overflow: hidden;
    }

    .table-header-info {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid #e2e8f0;
    }

    .table-title {
      margin: 0;
      font-size: 1rem;
      font-weight: 700;
      color: #0f172a;
    }

    .items-badge {
      background: #f1f5f9;
      color: #475569;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }

    .table-responsive {
      flex: 1;
      overflow-y: auto;
      max-height: calc(100vh - 350px);
    }

    .pos-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }

    .pos-table th {
      position: sticky;
      top: 0;
      background: #f8fafc;
      padding: 0.75rem 1rem;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #64748b;
      border-bottom: 1px solid #e2e8f0;
      z-index: 10;
    }

    .pos-table td {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }

    .item-name {
      font-weight: 600;
      color: #0f172a;
    }

    .item-meta {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      margin-top: 0.25rem;
    }

    .meta-tag {
      background: #f1f5f9;
      color: #475569;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 600;
    }

    .meta-sku {
      color: #94a3b8;
      font-size: 0.72rem;
      font-family: monospace;
    }

    .num-font {
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
    }

    .font-bold {
      font-weight: 700;
      color: #0f172a;
    }

    .text-right {
      text-align: right;
    }

    .text-center {
      text-align: center;
    }

    /* Stepper táctil para cantidad */
    .qty-stepper {
      display: inline-flex;
      align-items: center;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .btn-qty {
      width: 32px;
      height: 32px;
      border: 0;
      background: #f8fafc;
      color: #0f172a;
      font-size: 1.1rem;
      font-weight: 700;
      cursor: pointer;
      display: grid;
      place-items: center;
      transition: background 0.15s ease;
    }

    .btn-qty:hover {
      background: #e2e8f0;
    }

    .qty-val {
      min-width: 34px;
      text-align: center;
      font-weight: 700;
      font-size: 0.95rem;
    }

    .btn-row-del {
      background: transparent;
      border: 0;
      cursor: pointer;
      font-size: 1.1rem;
      opacity: 0.6;
      transition: opacity 0.2s ease;
    }

    .btn-row-del:hover {
      opacity: 1;
    }

    .empty-state {
      padding: 4rem 1.5rem;
      text-align: center;
    }

    .empty-illustration {
      font-size: 3rem;
      margin-bottom: 0.75rem;
      opacity: 0.6;
    }

    .empty-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #334155;
      margin-bottom: 0.35rem;
    }

    .empty-desc {
      font-size: 0.85rem;
      color: #94a3b8;
      max-width: 320px;
      margin: 0 auto;
    }

    .table-footer-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.85rem 1.25rem;
      border-top: 1px solid #e2e8f0;
      background: #f8fafc;
    }

    .btn-reset-order {
      background: transparent;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 0.4rem 0.8rem;
      font-size: 0.8rem;
      color: #64748b;
      cursor: pointer;
    }

    .btn-reset-order:hover:not(:disabled) {
      background: #fee2e2;
      border-color: #fca5a5;
      color: #ef4444;
    }

    .subtotal-indicator {
      font-size: 0.9rem;
      color: #475569;
      display: flex;
      gap: 0.5rem;
    }

    /* ------------------------------------------------------------------------
       PANEL DERECHO: TOTALES Y COBRO
       ------------------------------------------------------------------------ */
    .pos-right-panel {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .total-display-card {
      background: linear-gradient(135deg, #0b1120 0%, #1e293b 100%);
      color: #ffffff;
      border-radius: 12px;
      padding: 1.25rem;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.2);
    }

    .total-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .total-title {
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      color: #94a3b8;
    }

    .iva-pill {
      background: rgba(255, 255, 255, 0.1);
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.7rem;
      color: #cbd5e1;
    }

    .total-amount-row {
      display: flex;
      align-items: baseline;
      justify-content: flex-end;
      gap: 0.5rem;
    }

    .currency-symbol {
      font-size: 1.3rem;
      font-weight: 600;
      color: #f43f5e;
    }

    .total-number {
      font-size: 2.8rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
    }

    .checkout-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.1rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .card-title-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.85rem;
    }

    .card-title-row h4 {
      margin: 0;
      font-size: 0.92rem;
      font-weight: 700;
      color: #0f172a;
    }

    /* Tabs Cliente */
    .client-type-tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem;
      background: #f1f5f9;
      padding: 0.25rem;
      border-radius: 8px;
      margin-bottom: 0.75rem;
    }

    .tab-btn {
      padding: 0.45rem;
      border: 0;
      border-radius: 6px;
      background: transparent;
      font-size: 0.82rem;
      font-weight: 600;
      color: #64748b;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .tab-btn.active {
      background: #ffffff;
      color: #0f172a;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    .client-form-grid {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .pos-input {
      width: 100%;
      height: 38px;
      padding: 0 0.75rem;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      font-size: 0.88rem;
      outline: none;
      box-sizing: border-box;
    }

    .pos-input:focus {
      border-color: #be185d;
    }

    /* Métodos de Pago */
    .payment-methods-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.5rem;
    }

    .payment-tile {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.35rem;
      padding: 0.75rem 0.5rem;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #f8fafc;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .payment-tile:hover {
      border-color: #cbd5e1;
    }

    .payment-tile.selected {
      background: #fdf2f8;
      border-color: #be185d;
      color: #be185d;
      box-shadow: 0 0 0 2px rgba(190, 24, 93, 0.15);
    }

    .tile-icon {
      font-size: 1.3rem;
    }

    .tile-label {
      font-size: 0.78rem;
      font-weight: 700;
    }

    /* Caja de Efectivo */
    .cash-calculator {
      margin-top: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
    }

    .input-label {
      font-size: 0.8rem;
      font-weight: 600;
      color: #475569;
    }

    .cash-input-box {
      display: flex;
      align-items: center;
      border: 2px solid #cbd5e1;
      border-radius: 8px;
      padding: 0 0.75rem;
      background: #ffffff;
    }

    .cash-input-box:focus-within {
      border-color: #be185d;
    }

    .cash-input-box .prefix {
      font-size: 0.9rem;
      font-weight: 700;
      color: #64748b;
      margin-right: 0.5rem;
    }

    .cash-input {
      flex: 1;
      height: 42px;
      border: 0;
      outline: none;
      font-size: 1.3rem;
      font-weight: 800;
      color: #0f172a;
    }

    .quick-cash-row {
      display: flex;
      gap: 0.4rem;
    }

    .btn-quick-cash {
      flex: 1;
      padding: 0.4rem 0.2rem;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #ffffff;
      font-size: 0.8rem;
      font-weight: 700;
      color: #334155;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-quick-cash:hover {
      background: #f1f5f9;
      border-color: #94a3b8;
    }

    .change-card {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      color: #065f46;
    }

    .change-card.negative {
      background: #fef2f2;
      border-color: #fecaca;
      color: #b91c1c;
    }

    .change-label {
      font-size: 0.85rem;
      font-weight: 600;
    }

    .change-amount {
      font-size: 1.25rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
    }

    .qr-payment-box {
      margin-top: 0.85rem;
    }

    /* Botón Finalizar Cobro */
    .btn-charge-main {
      height: 56px;
      border: 0;
      border-radius: 12px;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #ffffff;
      font-size: 1.05rem;
      font-weight: 800;
      letter-spacing: 0.02em;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
      transition: all 0.2s ease;
    }

    .btn-charge-main:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45);
    }

    .btn-charge-main:disabled {
      background: #cbd5e1;
      color: #94a3b8;
      cursor: not-allowed;
      box-shadow: none;
      transform: none;
    }

    /* ------------------------------------------------------------------------
       MODAL TICKET TÉRMICO (80mm REALISTA)
       ------------------------------------------------------------------------ */
    .ticket-modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(4px);
      display: grid;
      place-items: center;
      z-index: 100;
      padding: 1rem;
    }

    .ticket-modal-card {
      background: #ffffff;
      border-radius: 16px;
      padding: 1.5rem;
      max-width: 440px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }

    .thermal-receipt {
      background: #fffffb;
      border: 1px dashed #cbd5e1;
      border-radius: 4px;
      padding: 1.5rem 1.25rem;
      font-family: 'Courier New', Courier, monospace;
      color: #111827;
      font-size: 0.8rem;
      line-height: 1.35;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }

    .receipt-header {
      text-align: center;
    }

    .receipt-brand {
      margin: 0 0 0.25rem 0;
      font-size: 1.05rem;
      font-weight: 800;
      letter-spacing: 0.05em;
    }

    .receipt-sub {
      font-size: 0.75rem;
    }

    .receipt-divider {
      color: #9ca3af;
      margin: 0.4rem 0;
      overflow: hidden;
      white-space: nowrap;
    }

    .receipt-title {
      font-weight: 700;
      font-size: 0.85rem;
    }

    .receipt-number {
      font-weight: 700;
    }

    .receipt-date {
      font-size: 0.72rem;
    }

    .item-head {
      display: flex;
      justify-content: space-between;
      font-weight: 700;
      margin-bottom: 0.3rem;
    }

    .receipt-item-line {
      display: flex;
      justify-content: space-between;
      margin-bottom: 0.25rem;
    }

    .it-desc {
      flex: 1;
      padding-right: 0.5rem;
    }

    .it-price {
      white-space: nowrap;
      font-weight: 600;
    }

    .tot-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 0.2rem;
    }

    .tot-row.main-total {
      font-size: 0.95rem;
      font-weight: 800;
      border-top: 1px dashed #64748b;
      border-bottom: 1px dashed #64748b;
      padding: 0.3rem 0;
      margin: 0.35rem 0;
    }

    .receipt-footer {
      text-align: center;
      margin-top: 0.75rem;
    }

    .qr-placeholder {
      margin: 0.75rem 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.35rem;
    }

    .qr-mock {
      width: 72px;
      height: 72px;
      border: 2px solid #000;
      display: grid;
      place-items: center;
      font-size: 2.2rem;
    }

    .qr-hash {
      font-size: 0.62rem;
      color: #4b5563;
    }

    .tributary-legend {
      font-size: 0.65rem;
      font-style: italic;
      color: #4b5563;
      margin: 0.5rem 0;
    }

    .gracias-msg {
      font-weight: 800;
      font-size: 0.85rem;
      margin-top: 0.5rem;
    }

    .modal-buttons-row {
      display: flex;
      gap: 0.75rem;
      margin-top: 1.25rem;
    }

    .btn-print {
      flex: 1;
      height: 44px;
      border: 0;
      border-radius: 8px;
      background: #0f172a;
      color: #ffffff;
      font-weight: 700;
      font-size: 0.9rem;
      cursor: pointer;
    }

    .btn-print:hover {
      background: #1e293b;
    }

    .btn-new-sale {
      flex: 1;
      height: 44px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      background: #ffffff;
      color: #0f172a;
      font-weight: 700;
      font-size: 0.9rem;
      cursor: pointer;
    }

    .btn-new-sale:hover {
      background: #f8fafc;
    }

    /* Animaciones */
    .animate-shake {
      animation: shake 0.3s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
    }

    @keyframes shake {
      10%, 90% { transform: translate3d(-1px, 0, 0); }
      20%, 80% { transform: translate3d(2px, 0, 0); }
      30%, 50%, 70% { transform: translate3d(-3px, 0, 0); }
      40%, 60% { transform: translate3d(3px, 0, 0); }
    }

    .animate-fade-in {
      animation: fadeIn 0.2s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Responsive */
    @media (max-width: 1024px) {
      .pos-container {
        grid-template-columns: 1fr;
      }
    }
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
  subtotalNeto = 0;
  referenciaPago = '';
  mensajeError = '';
  procesandoCobro = false;
  ticketImprimir: any = null;

  constructor(
    private readonly posService: PosService,
    private readonly pagoService: PagoService
  ) {}

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

  incrementarCantidad(index: number): void {
    this.lineas[index].cantidad += 1;
    this.recalcularLineas();
  }

  decrementarCantidad(index: number): void {
    if (this.lineas[index].cantidad > 1) {
      this.lineas[index].cantidad -= 1;
      this.recalcularLineas();
    } else {
      this.quitarLinea(index);
    }
  }

  recalcularLineas(): void {
    let subtotal = 0;
    this.lineas.forEach((l) => {
      l.subtotal = l.precio_unitario * l.cantidad;
      subtotal += l.subtotal;
    });
    this.subtotalNeto = subtotal;
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

  setMontoExacto(): void {
    this.montoRecibido = Math.ceil(this.totalAPagar);
    this.calcularCambio();
  }

  sumarEfectivo(monto: number): void {
    this.montoRecibido = (this.montoRecibido || 0) + monto;
    this.calcularCambio();
  }

  quitarLinea(index: number): void {
    this.lineas.splice(index, 1);
    this.recalcularLineas();
  }

  cobrarVenta(): void {
    if (this.procesandoCobro || this.lineas.length === 0) return;
    this.mensajeError = '';
    this.procesandoCobro = true;
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

    this.posService
      .registrarVenta(payload)
      .pipe(
        switchMap((resp) => {
          if (this.metodoPago === 'tarjeta' && resp.estado === 'pendiente_pago') {
            const pagoId = resp.intencion_pago?.pago_id;
            if (!pagoId) {
              return throwError(() => new Error('No se recibió el identificador de pago Stripe para confirmar el cobro con tarjeta.'));
            }
            return this.pagoService.conciliarPago(pagoId, 'pm_card_visa').pipe(
              switchMap((estado) => {
                if (estado.venta_estado === 'completada' || estado.pago_estado === 'completado') {
                  return of(resp);
                }
                return throwError(
                  () => new Error(estado.mensaje_error || `El cobro con tarjeta quedó pendiente (${estado.pago_estado || estado.venta_estado}).`)
                );
              })
            );
          }
          return of(resp);
        })
      )
      .subscribe({
        next: (resp) => {
          this.procesandoCobro = false;
          this.posService.imprimirTicket(resp.venta_id).subscribe({
            next: (ticketData) => {
              const t = ticketData?.ticket ?? ticketData;
              this.ticketImprimir = t
                ? {
                    ...t,
                    empresa_nombre: t.empresa_nombre ?? t.empresa,
                    empresa_nit: t.empresa_nit ?? t.nit,
                    sucursal_nombre: t.sucursal_nombre ?? t.sucursal,
                    sucursal_direccion: t.sucursal_direccion ?? t.direccion,
                    fecha_hora: t.fecha_hora ?? t.fecha,
                    cliente_nombre: t.cliente_nombre ?? t.cliente,
                    cliente_documento: t.cliente_documento ?? t.documento,
                  }
                : null;
            },
            error: () => {
              // Fallback elegante en caso de offline
              this.ticketImprimir = {
                empresa_nombre: 'FASHION STORE S.A.',
                numero: resp.numero || 'VENTA-' + resp.venta_id.slice(0, 8),
                fecha_hora: new Date(),
                total: this.totalAPagar,
              };
            },
          });
        },
        error: (err) => {
          this.procesandoCobro = false;
          this.mensajeError =
            err instanceof Error
              ? err.message
              : apiErrorMessage(err, 'Error al procesar cobro en mostrador');
        },
      });
  }

  imprimirTicket(): void {
    window.print();
  }

  reiniciarVenta(): void {
    this.lineas = [];
    this.totalAPagar = 0;
    this.subtotalNeto = 0;
    this.montoRecibido = 0;
    this.cambio = 0;
    this.ticketImprimir = null;
    this.scannerInput?.nativeElement?.focus();
  }
}
