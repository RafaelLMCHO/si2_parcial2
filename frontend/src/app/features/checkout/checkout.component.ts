import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { switchMap } from 'rxjs';
import { CatalogoService } from '../../core/catalogo.service';
import { CheckoutService } from '../../core/checkout.service';
import { apiErrorMessage } from '../../core/error-mapper';
import { InventarioService } from '../../core/inventario.service';
import { Carrito, DireccionCliente } from '../../core/models';
import { PagoService } from '../../core/pago.service';
import { SessionStoreService } from '../../core/session-store.service';

interface SucursalCheckoutOpcion {
  id: string;
  nombre: string;
  ciudad: string;
  stock: number;
}

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <div class="checkout-page">
      <h2>Carrito y Checkout Digital</h2>

      <!-- Paso 1: Carrito -->
      <div class="card" *ngIf="paso === 1">
        <h3>Tu Carrito de Compras</h3>
        <div *ngIf="errorPaso1" class="alert alert-error">⚠️ {{ errorPaso1 }}</div>
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
          Tu carrito está vacío. Agrega prendas desde el <a routerLink="/catalogo">catálogo</a>.
        </div>

        <div class="cart-total" *ngIf="carrito && carrito.items.length > 0">
          <h4>Total: {{ carrito.total | currency:'BOB ':'symbol':'1.2-2' }}</h4>
          <button class="btn btn-primary" (click)="iniciarCheckout()">Iniciar Compra →</button>
        </div>
      </div>

      <!-- Paso 2: Opciones de Entrega y Totales -->
      <div class="card" *ngIf="paso === 2">
        <h3>Paso 2: Tipo de Entrega</h3>
        <div *ngIf="errorPaso2" class="alert alert-error">⚠️ {{ errorPaso2 }}</div>

        <form [formGroup]="entregaForm">
          <div class="delivery-toggle">
            <label>
              <input type="radio" value="recojo" formControlName="tipo_entrega" (change)="onEntregaOptionChange()" /> Recojo en tienda física (Gratis)
            </label>
            <label>
              <input type="radio" value="envio" formControlName="tipo_entrega" (change)="onEntregaOptionChange()" /> Envío a domicilio (+20 BOB)
            </label>
          </div>

          <div class="form-group" *ngIf="entregaForm.get('tipo_entrega')?.value === 'recojo'">
            <div class="field-header">
              <label>Seleccionar Sucursal de Recojo:</label>
              <button type="button" class="link-btn" (click)="modoManualSucursal = !modoManualSucursal">
                {{ modoManualSucursal ? 'Usar lista de sucursales' : 'Ingresar UUID manual' }}
              </button>
            </div>
            <select
              *ngIf="!modoManualSucursal && sucursalesDisponibles.length > 0"
              formControlName="sucursal_id"
              class="form-control"
              (change)="onEntregaOptionChange()"
            >
              <option *ngFor="let s of sucursalesDisponibles" [value]="s.id">
                {{ s.nombre }}{{ s.ciudad ? ' (' + s.ciudad + ')' : '' }} — Stock ref: {{ s.stock }} disp.
              </option>
            </select>
            <input
              *ngIf="modoManualSucursal || sucursalesDisponibles.length === 0"
              formControlName="sucursal_id"
              class="form-control"
              placeholder="UUID de sucursal de recojo"
              (change)="onEntregaOptionChange()"
            />
          </div>

          <div class="form-group" *ngIf="entregaForm.get('tipo_entrega')?.value === 'envio'">
            <div class="field-header">
              <label>Seleccionar Dirección de Envío:</label>
              <button type="button" class="link-btn" (click)="modoManualDireccion = !modoManualDireccion">
                {{ modoManualDireccion ? 'Usar direcciones guardadas' : 'Ingresar UUID manual' }}
              </button>
            </div>
            <select
              *ngIf="!modoManualDireccion && direccionesGuardadas.length > 0"
              formControlName="direccion_id"
              class="form-control"
              (change)="onEntregaOptionChange()"
            >
              <option *ngFor="let d of direccionesGuardadas" [value]="d.id">
                {{ d.etiqueta || 'Dirección' }} — {{ d.linea1 }} ({{ d.ciudad }}){{ d.es_principal ? ' [Principal]' : '' }}
              </option>
            </select>
            <ng-container *ngIf="modoManualDireccion || direccionesGuardadas.length === 0">
              <input
                formControlName="direccion_id"
                class="form-control"
                placeholder="UUID de dirección registrada"
                (change)="onEntregaOptionChange()"
              />
              <small *ngIf="direccionesGuardadas.length === 0" class="helper-warn">
                No tienes direcciones registradas; ingresa un UUID válido o selecciona "Recojo en tienda física (Gratis)".
              </small>
            </ng-container>
          </div>

          <div class="form-group">
            <label>Cupón de Descuento (Opcional):</label>
            <div class="coupon-row">
              <input formControlName="cupon" class="form-control" placeholder="Ej: VERANO20" />
              <button type="button" class="btn btn-secondary btn-sm" (click)="validarTotales()">Aplicar Cupón</button>
            </div>
          </div>
        </form>

        <div *ngIf="resumenTotales?.lineas_faltantes?.length > 0" class="alert alert-error">
          ⚠️ Hay {{ resumenTotales.lineas_faltantes.length }} producto(s) sin stock suficiente en la sucursal seleccionada. Cambia de sucursal o ajusta la cantidad en tu carrito.
        </div>

        <div *ngIf="resumenTotales" class="resumen-box">
          <p *ngIf="resumenTotales.sucursal_despacho_nombre">
            Sucursal de despacho: <strong>{{ resumenTotales.sucursal_despacho_nombre }}</strong>
          </p>
          <p>Subtotal: {{ resumenTotales.subtotal | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <p *ngIf="resumenTotales.descuento > 0">Descuento: -{{ resumenTotales.descuento | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <p>IVA (13%): {{ resumenTotales.impuesto | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <p>Envío: {{ resumenTotales.costo_envio | currency:'BOB ':'symbol':'1.2-2' }}</p>
          <h4>Total a Pagar: {{ resumenTotales.total_a_pagar | currency:'BOB ':'symbol':'1.2-2' }}</h4>
        </div>

        <div class="btn-row">
          <button class="btn btn-outline" (click)="paso = 1">← Volver al Carrito</button>
          <button class="btn btn-primary" (click)="crearOrden()" [disabled]="creandoOrden">
            {{ creandoOrden ? 'Creando orden...' : 'Continuar al Pago →' }}
          </button>
        </div>
      </div>

      <!-- Paso 3: Pago Seguro Stripe (CU-24) -->
      <div class="card" *ngIf="paso === 3">
        <h3>Paso 3: Pago Seguro con Tarjeta (Stripe Sandbox)</h3>

        <div *ngIf="errorPago" class="alert alert-error">
          ⚠️ {{ errorPago }}
          <button class="btn btn-outline btn-sm" (click)="reintentarPago()" [disabled]="procesandoPago">Reintentar Cobro</button>
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
        <div *ngIf="errorComprobante" class="alert alert-error">⚠️ {{ errorComprobante }}</div>

        <div class="actions">
          <button class="btn btn-primary" (click)="descargarFactura('pdf')">Descargar Comprobante PDF</button>
          <button class="btn btn-outline" (click)="reiniciarCheckout()">Nueva Compra</button>
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
    .field-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .link-btn { background: none; border: none; color: #2563eb; font-size: 0.82rem; cursor: pointer; text-decoration: underline; padding: 0; }
    .coupon-row { display: flex; gap: 8px; align-items: center; }
    .helper-warn { display: block; margin-top: 4px; color: #b45309; font-size: 0.82rem; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .resumen-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin: 16px 0; }
    .resumen-box p { margin: 4px 0; font-size: 0.9rem; }
    .btn { padding: 8px 16px; border-radius: 6px; border: 1px solid transparent; cursor: pointer; font-size: 0.9rem; font-weight: 500; }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-secondary { background: #64748b; color: #fff; white-space: nowrap; }
    .btn-success { background: #10b981; color: #fff; }
    .btn-outline { border-color: #cbd5e1; background: #fff; }
    .btn-danger { background: #ef4444; color: #fff; }
    .btn-xs { padding: 2px 6px; font-size: 0.75rem; }
    .btn-sm { padding: 6px 10px; font-size: 0.82rem; }
    .btn-block { width: 100%; margin-top: 12px; }
    .btn-row { display: flex; justify-content: space-between; margin-top: 16px; }
    .actions { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }
    .stripe-mock-box { border: 1px dashed #6366f1; padding: 16px; border-radius: 8px; background: #eef2ff; margin-top: 14px; }
    .badge-test { background: #c7d2fe; color: #3730a3; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .confirmation-card { text-align: center; padding: 40px; }
    .success-icon { font-size: 3rem; color: #10b981; margin-bottom: 12px; }
    .alert-error { background: #fee2e2; color: #991b1b; padding: 12px; border-radius: 6px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  `]
})
export class CheckoutComponent implements OnInit {
  carrito: Carrito | null = null;
  paso = 1;
  entregaForm: FormGroup;
  resumenTotales: any = null;
  ordenCreada: any = null;
  sucursalesDisponibles: SucursalCheckoutOpcion[] = [];
  direccionesGuardadas: DireccionCliente[] = [];
  modoManualSucursal = false;
  modoManualDireccion = false;
  creandoOrden = false;
  procesandoPago = false;
  errorPaso1 = '';
  errorPaso2 = '';
  errorPago = '';
  errorComprobante = '';
  private ordenIdempotencyKey = '';
  private pagoIdempotencyKey = '';

  constructor(
    private readonly checkoutService: CheckoutService,
    private readonly pagoService: PagoService,
    private readonly catalogoService: CatalogoService,
    private readonly inventarioService: InventarioService,
    private readonly sessionStore: SessionStoreService,
    private readonly fb: FormBuilder
  ) {
    this.entregaForm = this.fb.group({
      tipo_entrega: ['recojo', Validators.required],
      sucursal_id: [''],
      direccion_id: [''],
      cupon: [''],
    });
  }

  ngOnInit(): void {
    this.cargarCarrito();
    this.cargarDirecciones();
  }

  cargarCarrito(): void {
    this.errorPaso1 = '';
    this.checkoutService.getCarrito().subscribe({
      next: (resp) => {
        this.carrito = resp;
        this.cargarSucursalesDisponibles(resp.items || []);
      },
      error: (err) => {
        this.errorPaso1 = apiErrorMessage(err, 'No se pudo cargar tu carrito de compras.');
      },
    });
  }

  private cargarDirecciones(): void {
    this.checkoutService.listarDirecciones().subscribe({
      next: (resp) => {
        const items = resp?.items || [];
        this.direccionesGuardadas = items;
        if (items.length > 0 && !this.entregaForm.get('direccion_id')?.value) {
          const principal = items.find((d) => d.es_principal) || items[0];
          this.entregaForm.patchValue({ direccion_id: principal.id });
        }
      },
      error: () => {
        this.direccionesGuardadas = [];
      },
    });
  }

  private cargarSucursalesDisponibles(items: Carrito['items']): void {
    const slug = this.sessionStore.readTenant() || 'demo';
    this.catalogoService.consultarCatalogo({ empresa_slug: slug }).subscribe({
      next: (cat) => {
        if (!cat.items || cat.items.length === 0) return;

        const varIds = new Set(items.map((i) => i.variante_id).filter(Boolean));
        const skus = new Set(items.map((i) => i.sku).filter(Boolean));
        const prendaObjetivo =
          cat.items.find((p) => (p.variantes || []).some((v) => varIds.has(v.id) || skus.has(v.sku))) ||
          cat.items[0];

        if (!prendaObjetivo?.id) return;

        this.inventarioService.consultarDisponibilidad(prendaObjetivo.id).subscribe({
          next: (disp) => {
            const firstItem = items[0];
            const opciones: SucursalCheckoutOpcion[] = (disp.sucursales || []).map((s) => {
              let stock = 0;
              if (firstItem) {
                const match = (s.variantes || []).find(
                  (v) => v.variante_id === firstItem.variante_id || (firstItem.sku && v.sku === firstItem.sku)
                );
                stock = match ? Number(match.stock_disponible || 0) : 0;
              } else {
                stock = (s.variantes || []).reduce((acc, v) => acc + Number(v.stock_disponible || 0), 0);
              }
              return {
                id: s.sucursal_id,
                nombre: s.nombre,
                ciudad: s.ciudad || '',
                stock,
              };
            });

            this.sucursalesDisponibles = opciones;
            const currentSuc = String(this.entregaForm.get('sucursal_id')?.value || '').trim();
            if (!currentSuc || !opciones.some((o) => o.id === currentSuc)) {
              const preferred = opciones.find((o) => o.stock > 0) || opciones[0];
              if (preferred) {
                this.entregaForm.patchValue({ sucursal_id: preferred.id });
              }
            }
            if (this.paso === 2) {
              this.validarTotales(true);
            }
          },
          error: () => {},
        });
      },
      error: () => {},
    });
  }

  cambiarCantidad(itemId: string, event: any): void {
    const qty = Number(event.target.value);
    if (qty > 0) {
      this.errorPaso1 = '';
      this.checkoutService.actualizarCantidad(itemId, qty).subscribe({
        next: (resp) => {
          this.carrito = resp;
          this.ordenCreada = null;
          this.ordenIdempotencyKey = '';
          this.cargarSucursalesDisponibles(resp.items || []);
        },
        error: (err) => {
          this.errorPaso1 = apiErrorMessage(err, 'No se pudo actualizar la cantidad.');
        },
      });
    }
  }

  eliminarItem(itemId: string): void {
    this.errorPaso1 = '';
    this.checkoutService.eliminarItem(itemId).subscribe({
      next: (resp) => {
        this.carrito = resp;
        this.ordenCreada = null;
        this.ordenIdempotencyKey = '';
        this.cargarSucursalesDisponibles(resp.items || []);
      },
      error: (err) => {
        this.errorPaso1 = apiErrorMessage(err, 'No se pudo eliminar el artículo.');
      },
    });
  }

  iniciarCheckout(): void {
    this.errorPaso2 = '';
    this.paso = 2;
    this.validarTotales(true);
  }

  onEntregaOptionChange(): void {
    this.errorPaso2 = '';
    this.resumenTotales = null;
    this.ordenCreada = null;
    this.ordenIdempotencyKey = '';
    this.pagoIdempotencyKey = '';
    this.validarTotales(true);
  }

  private construirPayloadCheckout(): {
    tipo_entrega: 'envio' | 'recojo';
    direccion_id?: string;
    sucursal_id?: string;
    cupon?: string;
  } | null {
    const val = this.entregaForm.value;
    const tipoEntrega: 'envio' | 'recojo' = val.tipo_entrega === 'envio' ? 'envio' : 'recojo';
    const sucursalId = String(val.sucursal_id || '').trim();
    const direccionId = String(val.direccion_id || '').trim();
    const cupon = String(val.cupon || '').trim();

    if (tipoEntrega === 'recojo' && !sucursalId) {
      return null;
    }
    if (tipoEntrega === 'envio' && !direccionId) {
      return null;
    }

    const payload: {
      tipo_entrega: 'envio' | 'recojo';
      direccion_id?: string;
      sucursal_id?: string;
      cupon?: string;
    } = { tipo_entrega: tipoEntrega };

    if (tipoEntrega === 'recojo') {
      payload.sucursal_id = sucursalId;
    } else {
      payload.direccion_id = direccionId;
    }
    if (cupon) {
      payload.cupon = cupon;
    }
    return payload;
  }

  validarTotales(silent: boolean = false): void {
    const payload = this.construirPayloadCheckout();
    if (!payload) {
      if (!silent) {
        const tipo = this.entregaForm.get('tipo_entrega')?.value;
        this.errorPaso2 =
          tipo === 'envio'
            ? 'Selecciona o ingresa un UUID de dirección válido para envío.'
            : 'Selecciona una sucursal física para el recojo.';
      }
      return;
    }

    if (!silent) {
      this.errorPaso2 = '';
    }

    this.checkoutService.validarCheckout(payload).subscribe({
      next: (resp) => {
        this.resumenTotales = resp;
        this.errorPaso2 = '';
      },
      error: (err) => {
        if (!silent) {
          this.errorPaso2 = apiErrorMessage(err, 'No se pudieron validar los totales del checkout.');
        }
      },
    });
  }

  crearOrden(): void {
    const payload = this.construirPayloadCheckout();
    if (!payload) {
      const tipo = this.entregaForm.get('tipo_entrega')?.value;
      this.errorPaso2 =
        tipo === 'envio'
          ? 'El envío a domicilio requiere una dirección válida. Selecciona una dirección o elige Recojo en tienda.'
          : 'Selecciona una sucursal de recojo para continuar.';
      return;
    }

    if (this.resumenTotales?.lineas_faltantes?.length > 0) {
      this.errorPaso2 =
        'Stock insuficiente en la sucursal seleccionada. Elige otra sucursal o ajusta la cantidad.';
      return;
    }

    if (this.ordenCreada) {
      this.errorPago = '';
      this.paso = 3;
      return;
    }

    this.errorPaso2 = '';
    this.creandoOrden = true;
    if (!this.ordenIdempotencyKey) {
      this.ordenIdempotencyKey = crypto.randomUUID();
    }

    this.checkoutService.crearOrden(payload, this.ordenIdempotencyKey).subscribe({
      next: (resp) => {
        this.creandoOrden = false;
        this.ordenCreada = resp;
        this.errorPago = '';
        this.pagoIdempotencyKey = '';
        this.paso = 3;
      },
      error: (err) => {
        this.creandoOrden = false;
        this.errorPaso2 = apiErrorMessage(err, 'No se pudo generar la orden de compra.');
      },
    });
  }

  procesarCobroMock(): void {
    if (!this.ordenCreada || this.procesandoPago) return;
    this.procesandoPago = true;
    this.errorPago = '';

    if (!this.pagoIdempotencyKey) {
      this.pagoIdempotencyKey = crypto.randomUUID();
    }

    this.pagoService
      .crearIntencionPago(this.ordenCreada.venta_id, this.pagoIdempotencyKey)
      .pipe(switchMap((intencion) => this.pagoService.conciliarPago(intencion.pago_id, 'pm_card_visa')))
      .subscribe({
        next: (estado) => {
          this.procesandoPago = false;
          if (estado.venta_estado === 'completada' || estado.pago_estado === 'completado') {
            this.errorPago = '';
            this.paso = 4;
            return;
          }
          this.ordenCreada = { ...this.ordenCreada, estado: estado.venta_estado };
          if (estado.pago_estado === 'fallido' || estado.venta_estado === 'pago_fallido') {
            this.pagoIdempotencyKey = '';
          }
          this.errorPago =
            estado.mensaje_error ||
            `El pago quedó en estado "${estado.pago_estado || estado.venta_estado}". Intenta nuevamente.`;
        },
        error: (err) => {
          this.procesandoPago = false;
          this.errorPago = apiErrorMessage(err, 'Error al procesar el pago con Stripe.');
        },
      });
  }

  reintentarPago(): void {
    if (!this.ordenCreada || this.procesandoPago) return;
    this.pagoIdempotencyKey = '';

    if (this.ordenCreada.estado === 'pago_fallido') {
      this.checkoutService.reintentarPago(this.ordenCreada.venta_id).subscribe({
        next: (resp) => {
          this.ordenCreada = resp;
          this.errorPago = '';
          this.procesarCobroMock();
        },
        error: (err) => {
          this.errorPago = apiErrorMessage(err, 'No se pudo reiniciar el intento de pago.');
        },
      });
      return;
    }

    this.errorPago = '';
    this.procesarCobroMock();
  }

  descargarFactura(formato: 'pdf' | 'json'): void {
    if (!this.ordenCreada) return;
    this.errorComprobante = '';
    this.checkoutService.descargarComprobante(this.ordenCreada.venta_id, formato).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comprobante_${this.ordenCreada.numero}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        this.errorComprobante = apiErrorMessage(err, 'No se pudo descargar el comprobante PDF.');
      },
    });
  }

  reiniciarCheckout(): void {
    this.ordenCreada = null;
    this.resumenTotales = null;
    this.ordenIdempotencyKey = '';
    this.pagoIdempotencyKey = '';
    this.errorPaso1 = '';
    this.errorPaso2 = '';
    this.errorPago = '';
    this.errorComprobante = '';
    this.paso = 1;
    this.cargarCarrito();
  }
}

