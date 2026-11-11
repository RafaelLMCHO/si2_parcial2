import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';
import { CatalogoService } from '../../../core/catalogo.service';
import { CheckoutService } from '../../../core/checkout.service';
import { AuthService } from '../../../core/auth.service';
import { InventarioService } from '../../../core/inventario.service';
import { NetworkService } from '../../../core/network.service';
import { DisponibilidadPrendaResponse, Prenda, VariantePrenda } from '../../../core/models';

@Component({
  selector: 'app-detalle-producto',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="product-detail-page font-sans">
      <!-- TOAST DE CONFIRMACIÓN -->
      @if (toast()) {
        <div class="toast-box animate-fade-in" [class.toast-error]="toastError()">
          <span>{{ toastError() ? '⚠️' : '✓' }}</span>
          <span class="toast-msg">{{ toast() }}</span>
          @if (!toastError()) {
            <a routerLink="/checkout" class="toast-action-btn">
              Ir al Pago
            </a>
          }
          <button (click)="toast.set('')" class="toast-close-btn">✕</button>
        </div>
      }

      <div class="detail-container">
        <!-- NAVEGACIÓN SUPERIOR / BREADCRUMB -->
        <nav class="breadcrumb-nav">
          <a routerLink="/catalogo" class="back-link">
            ← Volver al Catálogo
          </a>
          <span class="sep">/</span>
          <span class="muted">{{ prenda()?.categoria_nombre || 'Prendas' }}</span>
          <span class="sep">/</span>
          <span class="current">{{ prenda()?.nombre || 'Detalle' }}</span>
        </nav>

        @if (cargando()) {
          <div class="loading-state">
            <div class="spinner"></div>
            <p>Cargando prenda exclusiva...</p>
          </div>
        } @else if (prenda(); as p) {
          <div class="detail-card">
            <!-- COLUMNA IMAGEN -->
            <div class="detail-img-box">
              <img
                [src]="getPrendaImg(p)"
                [alt]="p.nombre"
                (error)="onImgError($event, p)"
                class="detail-main-img"
              />

              <!-- Badges flotantes -->
              <div class="badges-overlay">
                <span class="badge-tag">
                  {{ p.categoria_nombre || 'General' }}
                </span>
                @if (p.temporada_nombre) {
                  <span class="badge-subtag">
                    {{ p.temporada_nombre }}
                  </span>
                }
              </div>
            </div>

            <!-- COLUMNA INFORMACIÓN Y COMPRA -->
            <div class="detail-info-col">
              <div>
                <div class="meta-row">
                  <span>{{ p.codigo }}</span>
                  @if (p.marca) { <span>• {{ p.marca }}</span> }
                </div>

                <h1 class="product-heading">
                  {{ p.nombre }}
                </h1>

                <!-- PRECIO -->
                <div class="price-box">
                  <span class="price-val">
                    BOB {{ (varianteSeleccionada()?.precio_venta || p.precio_base) | number:'1.2-2' }}
                  </span>
                  @if (varianteSeleccionada()) {
                    <span class="sku-pill">
                      SKU: {{ varianteSeleccionada()?.sku }}
                    </span>
                  }
                </div>

                <p class="product-desc">
                  {{ p.descripcion || 'Prenda confeccionada con estándares de alta calidad, diseño vanguardista y confort garantizado.' }}
                </p>

                <!-- SELECTOR DE VARIANTES (TALLA / COLOR) -->
                @if (p.variantes && p.variantes.length > 0) {
                  <div class="variant-section">
                    <span class="section-label">
                      Variantes Disponibles (Talla & Color):
                    </span>
                    <div class="variant-chips-list">
                      @for (v of p.variantes; track v.id) {
                        <button
                          type="button"
                          (click)="seleccionarVariante(v)"
                          [class.active]="varianteSeleccionada()?.id === v.id"
                          class="variant-btn"
                        >
                          @if (v.color_hex) {
                            <span class="mini-color-dot" [style.backgroundColor]="v.color_hex"></span>
                          }
                          <span>{{ v.talla_nombre || 'Talla' }}</span>
                          @if (v.color_nombre) {
                            <span class="color-text">({{ v.color_nombre }})</span>
                          }
                        </button>
                      }
                    </div>
                  </div>
                }

                <!-- SELECTOR DE CANTIDAD -->
                <div class="qty-row">
                  <span class="section-label">Cantidad:</span>
                  <div class="qty-control">
                    <button
                      type="button"
                      (click)="cambiarCantidad(-1)"
                      [disabled]="cantidad() <= 1"
                      class="qty-btn"
                    >
                      -
                    </button>
                    <span class="qty-num">
                      {{ cantidad() }}
                    </span>
                    <button
                      type="button"
                      (click)="cambiarCantidad(1)"
                      class="qty-btn"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>

              <!-- BOTONES DE COMPRA Y RESERVA -->
              <div class="actions-wrapper">
                <div class="main-buttons-grid">
                  <button
                    type="button"
                    (click)="agregarAlCarrito()"
                    [disabled]="!varianteSeleccionada() || guardando()"
                    class="btn-add-cart"
                  >
                    <span>🛍️</span>
                    <span>{{ guardando() ? 'Añadiendo...' : 'Añadir a la Bolsa' }}</span>
                  </button>

                  <button
                    type="button"
                    (click)="comprarAhora()"
                    [disabled]="!varianteSeleccionada() || guardando()"
                    class="btn-checkout"
                  >
                    <span>⚡ Comprar Ahora</span>
                  </button>
                </div>

                <div class="secondary-buttons-grid">
                  <a
                    [routerLink]="['/reservas/nueva']"
                    [queryParams]="{
                      prenda_id: p.id,
                      variante_id: varianteSeleccionada()?.id || null,
                      cantidad: cantidad()
                    }"
                    class="btn-secondary"
                  >
                    👗 {{ network.online() ? 'Reservar Probador (CU-19)' : 'Reservar Offline (CU-26)' }}
                  </a>
                  <a
                    [routerLink]="['/vestidor-virtual']"
                    class="btn-secondary"
                  >
                    ✨ Probar en Vestidor RA
                  </a>
                </div>

                @if (disponibilidad(); as disp) {
                  <div style="margin-top: 10px; padding: 12px; border-radius: 12px; background: #f8fafc; border: 1px solid #e2e8f0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                      <span style="font-size:0.75rem; font-weight:800; color:#334155; text-transform:uppercase;">
                        Disponibilidad por tienda {{ disp.es_local ? '(Stock Local)' : '' }}
                      </span>
                    </div>
                    @if (disp.sucursales.length === 0) {
                      <p style="font-size:0.78rem; color:#64748b; margin:0;">Sin existencias registradas en caché para esta prenda.</p>
                    } @else {
                      <div style="display:flex; flex-direction:column; gap:6px;">
                        @for (suc of disp.sucursales; track suc.sucursal_id) {
                          <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem;">
                            <span style="font-weight:600; color:#1e293b;">{{ suc.nombre }} @if (suc.ciudad) { <small style="color:#64748b;">({{ suc.ciudad }})</small> }</span>
                            <span style="font-weight:700;" [style.color]="stockEnSucursal(suc) > 0 ? '#059669' : '#64748b'">
                              {{ stockEnSucursal(suc) }} disp.
                            </span>
                          </div>
                        }
                      </div>
                    }
                  </div>
                }
              </div>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .product-detail-page {
      background: #fafbfc;
      min-height: 85vh;
      padding: 32px 20px;
      color: #0f172a;
    }
    .detail-container {
      max-width: 1100px;
      margin: 0 auto;
    }
    .breadcrumb-nav {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      color: #64748b;
      margin-bottom: 24px;
    }
    .back-link {
      color: #4f46e5;
      text-decoration: none;
      font-weight: 700;
    }
    .sep { color: #cbd5e1; }
    .current { color: #0f172a; font-weight: 700; }
    .detail-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 24px;
      padding: 36px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 40px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    @media (max-width: 850px) {
      .detail-card {
        grid-template-columns: 1fr;
        padding: 24px;
        gap: 28px;
      }
    }
    .detail-img-box {
      position: relative;
      border-radius: 20px;
      overflow: hidden;
      background: #e2e8f0;
      min-height: 420px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .detail-main-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      max-height: 520px;
      display: block;
    }
    .badges-overlay {
      position: absolute;
      top: 14px;
      left: 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .badge-tag {
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(4px);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 800;
      color: #0f172a;
    }
    .badge-subtag {
      background: rgba(15,23,42,0.8);
      backdrop-filter: blur(4px);
      color: #ffffff;
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 0.7rem;
      font-weight: 700;
    }
    .detail-info-col {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 24px;
    }
    .meta-row {
      font-size: 0.75rem;
      font-weight: 800;
      text-transform: uppercase;
      color: #94a3b8;
      margin-bottom: 6px;
    }
    .product-heading {
      font-size: 1.85rem;
      font-weight: 900;
      color: #0f172a;
      margin: 0 0 14px 0;
      line-height: 1.25;
    }
    .price-box {
      display: flex;
      align-items: baseline;
      gap: 14px;
      padding-bottom: 18px;
      border-bottom: 1px solid #f1f5f9;
      margin-bottom: 18px;
    }
    .price-val {
      font-size: 1.75rem;
      font-weight: 900;
      color: #4f46e5;
    }
    .sku-pill {
      font-size: 0.75rem;
      font-family: monospace;
      background: #f1f5f9;
      color: #475569;
      padding: 4px 10px;
      border-radius: 6px;
    }
    .product-desc {
      font-size: 0.9rem;
      color: #475569;
      line-height: 1.6;
      margin: 0 0 24px 0;
    }
    .section-label {
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
      color: #64748b;
      margin-bottom: 8px;
      display: block;
    }
    .variant-chips-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .variant-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border: 2px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      cursor: pointer;
      font-size: 0.82rem;
      font-weight: 700;
      color: #334155;
      transition: all 0.15s;
    }
    .variant-btn.active {
      border-color: #4f46e5;
      background: #eef2ff;
      color: #4338ca;
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
    }
    .mini-color-dot {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 1px solid rgba(0,0,0,0.15);
      display: inline-block;
    }
    .color-text {
      font-size: 0.75rem;
      color: #64748b;
      font-weight: 500;
    }
    .qty-row {
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 20px 0;
    }
    .qty-control {
      display: inline-flex;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      overflow: hidden;
      background: #ffffff;
    }
    .qty-btn {
      border: none;
      background: #f8fafc;
      padding: 8px 16px;
      font-size: 1rem;
      font-weight: bold;
      color: #475569;
      cursor: pointer;
    }
    .qty-num {
      padding: 8px 18px;
      font-size: 0.95rem;
      font-weight: 800;
      background: #ffffff;
      border-left: 1px solid #cbd5e1;
      border-right: 1px solid #cbd5e1;
      min-width: 36px;
      text-align: center;
    }
    .actions-wrapper {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding-top: 18px;
      border-top: 1px solid #f1f5f9;
    }
    .main-buttons-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .btn-add-cart {
      padding: 14px;
      background: #eef2ff;
      color: #4338ca;
      border: 1px solid #c7d2fe;
      border-radius: 14px;
      font-size: 0.9rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-add-cart:hover {
      background: #e0e7ff;
    }
    .btn-checkout {
      padding: 14px;
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 14px;
      font-size: 0.9rem;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-checkout:hover {
      background: #4338ca;
    }
    .secondary-buttons-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .btn-secondary {
      padding: 10px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #475569;
      text-align: center;
      text-decoration: none;
      background: #ffffff;
      transition: background 0.15s;
    }
    .btn-secondary:hover {
      background: #f8fafc;
    }
    .toast-box {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #0f172a;
      color: #ffffff;
      padding: 14px 20px;
      border-radius: 14px;
      z-index: 99999;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .toast-error { background: #991b1b; }
    .toast-msg { font-size: 0.85rem; font-weight: 700; }
    .toast-action-btn {
      background: #4f46e5;
      color: #fff;
      font-size: 0.75rem;
      font-weight: 800;
      padding: 6px 12px;
      border-radius: 8px;
      text-decoration: none;
    }
    .toast-close-btn {
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
    }
    .loading-state {
      text-align: center;
      padding: 80px 20px;
      background: #ffffff;
      border-radius: 20px;
      border: 1px solid #e2e8f0;
    }
    .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid #e2e8f0;
      border-top-color: #4f46e5;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 12px auto;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in { animation: fadeIn 0.2s ease-out; }
  `]
})
export class DetalleProductoComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private catalogoService = inject(CatalogoService);
  private checkoutService = inject(CheckoutService);
  private inventarioService = inject(InventarioService);
  private cu25Offline = inject(CU25DescargarCatalogoOfflineController);
  readonly network = inject(NetworkService);
  private auth = inject(AuthService);

  cargando = signal(false);
  prenda = signal<Prenda | null>(null);
  varianteSeleccionada = signal<VariantePrenda | null>(null);
  disponibilidad = signal<DisponibilidadPrendaResponse | null>(null);
  cantidad = signal(1);
  guardando = signal(false);

  toast = signal('');
  toastError = signal(false);
  private toastTimer: any;

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.cargar(id);
    }
    this.cu25Offline.asegurarCatalogoOfflineCargado();
  }

  cargar(id: string) {
    this.cargando.set(true);
    this.catalogoService.obtenerPrendaPorId(id).subscribe({
      next: (res: Prenda) => {
        this.prenda.set(res);
        if (res.variantes && res.variantes.length > 0) {
          this.varianteSeleccionada.set(res.variantes[0]);
        }
        this.cargando.set(false);
        this.cargarDisponibilidad(id);
      },
      error: () => {
        this.cargando.set(false);
        this.mostrarToast('No se pudo cargar esta prenda sin conexión. Descarga o abre el catálogo en línea al menos una vez.', true);
      }
    });
  }

  cargarDisponibilidad(prendaId: string) {
    if (!this.auth.isAuthenticated() && this.network.online()) {
      return;
    }
    this.inventarioService.consultarDisponibilidad(prendaId).subscribe({
      next: (disp) => this.disponibilidad.set(disp),
      error: () => {},
    });
  }

  stockEnSucursal(suc: { variantes?: Array<{ variante_id: string; stock_disponible: number }> }): number {
    const varId = this.varianteSeleccionada()?.id;
    const vars = suc?.variantes || [];
    if (varId) {
      const match = vars.find((v) => v.variante_id === varId);
      if (match) return Number(match.stock_disponible || 0);
    }
    return vars.reduce((acc, v) => acc + Number(v.stock_disponible || 0), 0);
  }

  getPrendaImg(p: Prenda | { nombre?: string; categoria_nombre?: string; imagen_url?: string | null }): string {
    if (p.imagen_url && p.imagen_url.startsWith('http') && !p.imagen_url.includes('cdn.fashionstore.test')) {
      return p.imagen_url;
    }
    const n = (p.nombre || '').toLowerCase();
    const c = (p.categoria_nombre || '').toLowerCase();

    if (n.includes('camisa') || n.includes('lino') || c.includes('camisa')) {
      return 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80';
    }
    if (n.includes('blazer') || n.includes('traje') || c.includes('chaqueta')) {
      return 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=600&q=80';
    }
    if (n.includes('pijama') || c.includes('interior')) {
      return 'https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=600&q=80';
    }
    if (n.includes('vestido') || c.includes('vestido')) {
      return 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80';
    }
    if (n.includes('pantalon') || n.includes('jean') || c.includes('pantalon')) {
      return 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80';
    }
    if (c.includes('calzado') || n.includes('zapato')) {
      return 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80';
    }
    return 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';
  }

  onImgError(event: Event, p: any): void {
    const img = event.target as HTMLImageElement;
    img.src = 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';
  }

  seleccionarVariante(v: VariantePrenda) {
    this.varianteSeleccionada.set(v);
  }

  cambiarCantidad(delta: number) {
    this.cantidad.update((c) => Math.max(1, c + delta));
  }

  agregarAlCarrito() {
    const v = this.varianteSeleccionada();
    if (!v) {
      this.mostrarToast('Selecciona una talla o variante antes de continuar.', true);
      return;
    }

    if (!this.auth.isAuthenticated()) {
      this.mostrarToast('Por favor inicia sesión para comprar.', true);
      this.router.navigate(['/login']);
      return;
    }

    this.guardando.set(true);
    this.checkoutService.agregarAlCarrito(v.id, this.cantidad()).subscribe({
      next: () => {
        this.guardando.set(false);
        this.mostrarToast(`✓ ${this.cantidad()}x "${this.prenda()?.nombre}" agregado a tu bolsa.`);
      },
      error: (err) => {
        this.guardando.set(false);
        this.mostrarToast('Error al agregar al carrito: ' + (err.error?.detail?.message || err.message), true);
      }
    });
  }

  comprarAhora() {
    const v = this.varianteSeleccionada();
    if (!v) {
      this.mostrarToast('Selecciona una variante.', true);
      return;
    }

    if (!this.auth.isAuthenticated()) {
      this.mostrarToast('Inicia sesión para completar tu compra.', true);
      this.router.navigate(['/login']);
      return;
    }

    this.guardando.set(true);
    this.checkoutService.agregarAlCarrito(v.id, this.cantidad()).subscribe({
      next: () => {
        this.guardando.set(false);
        this.router.navigate(['/checkout']);
      },
      error: (err) => {
        this.guardando.set(false);
        this.mostrarToast('Error: ' + (err.error?.detail?.message || err.message), true);
      }
    });
  }

  mostrarToast(msg: string, esError = false) {
    this.toast.set(msg);
    this.toastError.set(esError);
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.toast.set(''), 4500);
  }
}
