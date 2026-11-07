import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CheckoutService } from '../../core/checkout.service';
import { Carrito } from '../../core/models';
import { PagoService } from '../../core/pago.service';

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="checkout-page">
      <h2>Carrito y Checkout Digital</h2>

      <!-- Paso 1: Carrito -->
      <div class="card" *ngIf="paso === 1">
        <h3>Tu Carrito de Compras</h3>
        <table class="table" *ngIf="carrito && carrito.items.length > 0">
          <thead>
            <tr>
              <th>Artículo</th>
              <th>Talla / Color</th>
              <th>Precio</th>
              <th>Cantidad</th>
              <th>Subtotal</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let it of carrito.items">
              <td><strong>{{ it.prenda_nombre }}</strong></td>
              <td>{{ it.talla }} / {{ it.color }}</td>
              <td>{{ it.precio_unitario | currency:'BOB ':'symbol':'1.2-2' }}</td>
              <td>
                <input type="number" [value]="it.cantidad" min="1" (change)="cambiarCantidad(it.id, $event)" class="qty-input" />
              </td>
              <td>{{ it.subtotal | currency:'BOB ':'symbol':'1.2-2' }}</td>
              <td>
                <button class="btn btn-danger btn-xs" (click)="eliminarItem(it.id)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div *ngIf="!carrito || carrito.items.length === 0" class="empty-state">
          Tu carrito está vacío. Agrega prendas desde el catálogo.
        </div>

        <div class="cart-total" *ngIf="carrito && carrito.items.length > 0">
          <h4>Total: {{ carrito.total | currency:'BOB ':'symbol':'1.2-2' }}</h4>
          <button class="btn btn-primary" (click)="iniciarCheckout()">Iniciar Compra →</button>
        </div>
      </div>

      <!-- Paso 2: Opciones de Entrega y Totales -->
      <div class="card" *ngIf="paso === 2">
        <h3>Paso 2: Tipo de Entrega</h3>
        <form [formGroup]="entregaForm">
          <div class="delivery-toggle">
            <label>
              <input type="radio" value="envio" formControlName="tipo_entrega" /> Envío a domicilio (+20 BOB)
            </label>
            <label>
              <input type="radio" value="recojo" formControlName="tipo_entrega" /> Recojo en tienda física (Gratis)
            </label>
          </div>

          <div class="form-group" *ngIf="entregaForm.get('tipo_entrega')?.value === 'recojo'">
            <label>Seleccionar Sucursal de Recojo:</label>
            <input formControlName="sucursal_id" class="form-control" placeholder="UUID de sucursal" />
          </div>

          <div class="form-group">
            <label>Cupón de Descuento (Opcional):</label>
            <input formControlName="cupon" class="form-control" placeholder="Ej: BIENVENIDO10" />
            <button type="button" class="btn btn-secondary btn-sm" (click)="validarTotales()">Aplicar Cupón</button>
          </div>
        </form>

        <div *ngIf="resumenTotales" class="resumen-box">
          <p>Subtotal: {{ resumenTotales.subtotal | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <p *ngIf="resumenTotales.descuento > 0">Descuento: -{{ resumenTotales.descuento | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <p>IVA (13%): {{ resumenTotales.impuesto | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <p>Envío: {{ resumenTotales.costo_envio | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <h4>Total a Pagar: {{ resumenTotales.total_a_pagar | currency:'BOB ':'symbol':'1.2-2' }}</h4>
        </div>

        <div class="btn-row">
          <button class="btn btn-outline" (click)="paso = 1">← Volver al Carrito</button>
          <button class="btn btn-primary" (click)="crearOrden()">Continuar al Pago →</button>
        </div>
      </div>

      <!-- Paso 3: Pago Seguro Stripe (CU-24) -->
      <div class="card" *ngIf="paso === 3">
        <h3>Paso 3: Pago Seguro con Tarjeta (Stripe Sandbox)</h3>

        <div *ngIf="errorPago" class="alert alert-error">
          ⚠️ {{ errorPago }}
          <button class="btn btn-outline btn-sm" (click)="reintentarPago()">Reintentar Cobro</button>
        </div>

        <div *ngIf="ordenCreada" class="orden-info">
          <p>Orden N°: <strong>{{ ordenCreada.numero }}</strong></p>
          <p>Monto a cobrar: <strong>{{ ordenCreada.total_a_pagar | currency:'BOB ':'symbol':'1.2-2' }}</strong></p>
        </div>

        <!-- Stripe Mock / Embebido -->
        <div class="stripe-mock-box">
          <p class="badge badge-test">Modo Sandbox Stripe</p>
          <label>Datos de tarjeta simulada:</label>
          <input type="text" class="form-control" value="4242 •••• •••• 4242" readonly />
          <button class="btn btn-success btn-block" (click)="procesarCobroMock()" [disabled]="procesandoPago">
            {{ procesandoPago ? 'Procesando con la entidad bancaria...' : 'Confirmar Pago Seguro' }}
          </button>
        </div>
      </div>

      <!-- Paso 4: Confirmación y Comprobante Digital -->
      <div class="card confirmation-card" *ngIf="paso === 4">
        <div class="success-icon">✓</div>
        <h3>¡Compra Completada Exitosamente!</h3>
        <p>Tu orden comercial y stock han sido confirmados en la plataforma.</p>
        <p>Orden N°: <strong>{{ ordenCreada?.numero }}</strong></p>

        <div class="actions">
          <button class="btn btn-primary" (click)="descargarFactura('pdf')">Descargar Comprobante PDF</button>
          <button class="btn btn-outline" (click)="paso = 1; cargarCarrito()">Nueva Compra</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .checkout-page { padding: 24px; max-width: 800px; margin: 0 auto; font-family: inherit; }
    .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
    .table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .table th, .table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; text-align: left; }
    .qty-input { width: 60px; padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px; }
    .cart-total { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; border-top: 1px solid #e2e8f0; padding-top: 16px; }
    .delivery-toggle label { display: block; margin-bottom: 8px; cursor: pointer; }
    .form-group { margin: 12px 0; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .resumen-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin: 16px 0; }
    .resumen-box p { margin: 4px 0; font-size: 0.9rem; }
    .btn { padding: 8px 16px; border-radius: 6px; border: 1px solid transparent; cursor: pointer; font-size: 0.9rem; font-weight: 500; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-secondary { background: #64748b; color: #fff; }
    .btn-success { background: #10b981; color: #fff; }
    .btn-outline { border-color: #cbd5e1; background: #fff; }
    .btn-danger { background: #ef4444; color: #fff; }
    .btn-xs { padding: 2px 6px; font-size: 0.75rem; }
    .btn-block { width: 100%; margin-top: 12px; }
    .btn-row { display: flex; justify-content: space-between; margin-top: 16px; }
    .stripe-mock-box { border: 1px dashed #6366f1; padding: 16px; border-radius: 8px; background: #eef2ff; margin-top: 14px; }
    .badge-test { background: #c7d2fe; color: #3730a3; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .confirmation-card { text-align: center; padding: 40px; }
    .success-icon { font-size: 3rem; color: #10b981; margin-bottom: 12px; }
    .alert-error { background: #fee2e2; color: #991b1b; padding: 12px; border-radius: 6px; margin-bottom: 14px; }
  `]
})
export class CheckoutComponent implements OnInit {
  carrito: Carrito | null = null;
  paso = 1;
  entregaForm: FormGroup;
  resumenTotales: any = null;
  ordenCreada: any = null;
  procesandoPago = false;
  errorPago = '';

  constructor(
    private readonly checkoutService: CheckoutService,
    private readonly pagoService: PagoService,
    private readonly fb: FormBuilder
  ) {
    this.entregaForm = this.fb.group({
      tipo_entrega: ['envio', Validators.required],
      sucursal_id: ['11111111-1111-1111-1111-111111111101'],
      cupon: [''],
    });
  }

  ngOnInit(): void {
    this.cargarCarrito();
  }

  cargarCarrito(): void {
    this.checkoutService.getCarrito().subscribe({
      next: (resp) => (this.carrito = resp),
    });
  }

  cambiarCantidad(itemId: string, event: any): void {
    const qty = Number(event.target.value);
    if (qty > 0) {
      this.checkoutService.actualizarCantidad(itemId, qty).subscribe({
        next: (resp) => (this.carrito = resp),
      });
    }
  }

  eliminarItem(itemId: string): void {
    this.checkoutService.eliminarItem(itemId).subscribe({
      next: (resp) => (this.carrito = resp),
    });
  }

  iniciarCheckout(): void {
    this.paso = 2;
    this.validarTotales();
  }

  validarTotales(): void {
    const val = this.entregaForm.value;
    this.checkoutService
      .validarCheckout({
        tipo_entrega: val.tipo_entrega,
        sucursal_id: val.sucursal_id,
        cupon: val.cupon,
      })
      .subscribe({
        next: (resp) => (this.resumenTotales = resp),
      });
  }

  crearOrden(): void {
    const val = this.entregaForm.value;
    const idempotencyKey = crypto.randomUUID();
    this.checkoutService
      .crearOrden(
        {
          tipo_entrega: val.tipo_entrega,
          sucursal_id: val.sucursal_id,
          cupon: val.cupon,
        },
        idempotencyKey
      )
      .subscribe({
        next: (resp) => {
          this.ordenCreada = resp;
          this.paso = 3;
        },
      });
  }

  procesarCobroMock(): void {
    if (!this.ordenCreada) return;
    this.procesandoPago = true;
    this.errorPago = '';

    const idempotencyKey = crypto.randomUUID();
    this.pagoService
      .crearIntencionPago(this.ordenCreada.venta_id, idempotencyKey)
      .subscribe({
        next: () => {
          setTimeout(() => {
            this.procesandoPago = false;
            this.paso = 4;
          }, 1200);
        },
        error: (err) => {
          this.procesandoPago = false;
          this.errorPago = err?.error?.detail?.message || 'Tarjeta rechazada o fondos insuficientes (5.a)';
        },
      });
  }

  reintentarPago(): void {
    this.checkoutService.reintentarPago(this.ordenCreada.venta_id).subscribe({
      next: () => {
        this.errorPago = '';
        this.procesarCobroMock();
      },
    });
  }

  descargarFactura(formato: 'pdf' | 'json'): void {
    if (!this.ordenCreada) return;
    this.checkoutService.descargarComprobante(this.ordenCreada.venta_id, formato).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comprobante_${this.ordenCreada.numero}.pdf`;
        a.click();
      },
    });
  }
}

