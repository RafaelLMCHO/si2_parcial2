import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { CatalogoService, CatalogFilterParams } from '../../core/catalogo.service';
import { AuxiliaresCatalogoResponse, Prenda, Variante, Carrito, CarritoItem } from '../../core/models';
import { NetworkService } from '../../core/network.service';
import { CheckoutService } from '../../core/checkout.service';
import { AuthService } from '../../core/auth.service';
import { SessionStoreService } from '../../core/session-store.service';
import { CU25DescargarCatalogoOfflineController } from '../../controller/cu25_descargar_catalogo_offline_controller';
import { CU38RecomendacionesIaController, OutfitRecomendado } from '../../controller/cu38_recomendaciones_ia_controller';

@Component({
  selector: 'app-catalogo-cliente',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="fashion-catalog font-sans">
      <!-- TOAST DE NOTIFICACIÓN -->
      @if (toastMensaje()) {
        <div class="toast-notification animate-fade-in" [class.toast-error]="toastEsError()">
          <div class="toast-content">
            <span class="toast-icon">{{ toastEsError() ? '⚠️' : '✓' }}</span>
            <span class="toast-text">{{ toastMensaje() }}</span>
          </div>
          <div class="toast-actions">
            @if (!toastEsError()) {
              <button (click)="abrirCarritoDrawer()" class="toast-btn">Ver Bolsa</button>
            }
            <button (click)="toastMensaje.set('')" class="toast-close">✕</button>
          </div>
        </div>
      }

      <!-- HERO BANNER BOUTIQUE -->
      <section class="hero-section">
        <div class="hero-inner">
          <div class="hero-text">
            <span class="hero-tag">Colección Exclusiva 2026</span>
            <h1 class="hero-title">Catálogo de Moda & Tendencias</h1>
            <p class="hero-subtitle">
              Diseños contemporáneos, cortes perfectos y materiales de primera calidad. Explora nuestro catálogo y personaliza tu estilo.
            </p>
          </div>

          <div class="hero-actions">
            <span
              class="network-pill"
              [class.network-online]="network.online()"
              [class.network-offline]="!network.online()"
            >
              <span class="dot-indicator"></span>
              {{ network.online() ? 'Tienda en Línea' : 'Catálogo Offline' }}
            </span>

            <!-- BOTÓN FLOTANTE / HEADER DEL CARRITO -->
            <button
              type="button"
              (click)="abrirCarritoDrawer()"
              class="cart-widget-btn"
              title="Ver bolsa de compras"
            >
              <div class="cart-icon-box">
                <span class="cart-emoji">🛍️</span>
                @if (totalItemsEnCarrito() > 0) {
                  <span class="badge-count">{{ totalItemsEnCarrito() }}</span>
                }
              </div>
              <div class="cart-btn-labels">
                <span class="cart-label-sub">Mi Bolsa</span>
                <span class="cart-label-amount">BOB {{ totalMontoEnCarrito() | number:'1.2-2' }}</span>
              </div>
            </button>
          </div>
        </div>
      </section>

      <!-- BARRA DE CATEGORÍAS RÁPIDAS (TABS HORIZONTALES) -->
      <nav class="category-navbar">
        <div class="category-navbar-inner">
          <button
            type="button"
            (click)="seleccionarCategoria(undefined)"
            [class.active]="!filtros.categoria_id"
            class="cat-tab"
          >
            ✨ Todos los Artículos
          </button>
          @for (cat of auxiliares().categorias; track cat.id) {
            <button
              type="button"
              (click)="seleccionarCategoria(cat.id.toString())"
              [class.active]="filtros.categoria_id === cat.id.toString()"
              class="cat-tab"
            >
              {{ cat.nombre }}
            </button>
          }
        </div>
      </nav>

      <!-- SECCIÓN BOUTIQUE AI STYLIST (CU-38: ASESOR PERSONAL DE MODA) -->
      <section class="ai-stylist-banner">
        <div class="stylist-inner">
          <div class="stylist-badge">
            <span class="sparkle-icon">✨</span>
            <span class="badge-text">PERSONAL STYLIST IA (CU-38)</span>
          </div>
          <h2 class="stylist-title">¿Para qué ocasión buscas tu outfit hoy?</h2>
          <p class="stylist-subtitle">Nuestra inteligencia artificial analiza las prendas disponibles del catálogo y crea combinaciones con armonía de corte, colorimetría y temporada.</p>

          <!-- Chips de Ocasión Rápida -->
          <div class="stylist-chips-row">
            <button type="button" class="stylist-chip" (click)="consultarOutfitIa('Cena elegante de noche en Santa Cruz')">
              🍸 Cena Romántica
            </button>
            <button type="button" class="stylist-chip" (click)="consultarOutfitIa('Look profesional para oficina y reuniones ejecutivas')">
              💼 Oficina & Negocios
            </button>
            <button type="button" class="stylist-chip" (click)="consultarOutfitIa('Outfit fresco de verano para clima caluroso')">
              ☀️ Verano Fresco
            </button>
            <button type="button" class="stylist-chip" (click)="consultarOutfitIa('Fiesta de gala o celebración formal de noche')">
              🎉 Fiesta & Gala
            </button>
            <button type="button" class="stylist-chip" (click)="consultarOutfitIa('Look casual chic cómodo para fin de semana')">
              ☕ Casual Chic
            </button>
          </div>

          <!-- Buscador en Lenguaje Natural -->
          <div class="stylist-input-row">
            <input
              type="text"
              [(ngModel)]="promptIa"
              (keyup.enter)="consultarOutfitIa(promptIa)"
              placeholder="Escribe tu ocasión: Ej. Boda civil de tarde, graduación, salida con amigas..."
              class="stylist-input"
            />
            <button
              type="button"
              class="btn-stylist-ask"
              (click)="consultarOutfitIa(promptIa)"
              [disabled]="stylistIa.cargando() || !promptIa.trim()"
            >
              @if (stylistIa.cargando()) {
                <span>⏳ Curando Look...</span>
              } @else {
                <span>✨ Armar Outfit IA</span>
              }
            </button>
          </div>
        </div>
      </section>

      <!-- CONTENEDOR PRINCIPAL -->
      <div class="catalog-container">
        <!-- BANNER OFFLINE (CU-13) -->
        @if (isOffline()) {
          <div class="offline-alert">
            <span class="text-2xl">📡</span>
            <div>
              <strong>Modo Sin Conexión:</strong>
              Estás visualizando el catálogo almacenado en caché local.
            </div>
          </div>
        }

        <!-- BARRA SUPERIOR DE HERRAMIENTAS: Búsqueda, Género, Ordenamiento y Conteo -->
        <div class="toolbar-box">
          <!-- Buscador -->
          <div class="search-input-wrapper">
            <span class="search-icon">🔍</span>
            <input
              type="text"
              [(ngModel)]="filtros.search"
              (ngModelChange)="onSearchChange()"
              placeholder="Buscar por prenda, estilo o marca..."
              class="search-input"
            />
            @if (filtros.search) {
              <button (click)="filtros.search = ''; aplicarFiltros()" class="btn-clear-search">✕</button>
            }
          </div>

          <!-- Píldoras de Género -->
          <div class="gender-pills-row">
            <button (click)="seleccionarGenero(undefined)" [class.active]="!filtros.genero" class="gender-btn">Todos</button>
            <button (click)="seleccionarGenero('mujer')" [class.active]="filtros.genero === 'mujer'" class="gender-btn">Mujer</button>
            <button (click)="seleccionarGenero('hombre')" [class.active]="filtros.genero === 'hombre'" class="gender-btn">Hombre</button>
            <button (click)="seleccionarGenero('nino')" [class.active]="filtros.genero === 'nino'" class="gender-btn">Niño</button>
            <button (click)="seleccionarGenero('unisex')" [class.active]="filtros.genero === 'unisex'" class="gender-btn">Unisex</button>
          </div>

          <!-- Selector de Ordenamiento -->
          <div class="sort-wrapper">
            <span class="total-counter"><strong>{{ prendasFiltradas().length }}</strong> prendas</span>
            <select [(ngModel)]="ordenSeleccionado" class="sort-select">
              <option value="relevancia">✨ Destacados</option>
              <option value="precio_asc">💵 Precio: Menor a Mayor</option>
              <option value="precio_desc">💎 Precio: Mayor a Menor</option>
              <option value="nombre_asc">🔤 Nombre: A - Z</option>
            </select>
          </div>
        </div>

        <div class="layout-grid">
          <!-- PANEL LATERAL DE FILTROS AVANZADOS -->
          <aside class="sidebar-filters">
            <div class="sidebar-card">
              <div class="sidebar-header">
                <h3 class="sidebar-title"><span>🎨</span> Filtros</h3>
                @if (hayFiltrosActivos()) {
                  <button (click)="limpiarFiltros()" class="btn-reset-filters">Limpiar todo</button>
                }
              </div>

              <!-- Filtro por Talla -->
              @if (auxiliares().tallas.length > 0) {
                <div class="filter-group">
                  <label class="filter-label">Tallas</label>
                  <div class="sizes-grid">
                    @for (t of auxiliares().tallas; track t.id) {
                      <button
                        type="button"
                        (click)="seleccionarTalla(t.id)"
                        [class.active]="filtros.talla_id === +t.id"
                        class="size-pill"
                      >
                        {{ t.nombre }}
                      </button>
                    }
                  </div>
                </div>
              }

              <!-- Filtro por Color -->
              @if (auxiliares().colores.length > 0) {
                <div class="filter-group">
                  <label class="filter-label">Colores</label>
                  <div class="colors-row">
                    @for (col of auxiliares().colores; track col.id) {
                      <button
                        type="button"
                        (click)="seleccionarColor(col.id)"
                        [title]="col.nombre"
                        [class.active]="filtros.color_id === +col.id"
                        class="color-circle"
                        [style.backgroundColor]="col.extra || '#ccc'"
                      >
                        @if (filtros.color_id === +col.id) {
                          <span class="color-check">✓</span>
                        }
                      </button>
                    }
                  </div>
                </div>
              }

              <!-- Filtro por Temporada -->
              @if (auxiliares().temporadas.length > 0) {
                <div class="filter-group">
                  <label class="filter-label">Temporada</label>
                  <select [(ngModel)]="filtros.temporada_id" (ngModelChange)="aplicarFiltros()" class="filter-select">
                    <option [ngValue]="undefined">Todas las temporadas</option>
                    @for (temp of auxiliares().temporadas; track temp.id) {
                      <option [value]="temp.id">{{ temp.nombre }}</option>
                    }
                  </select>
                </div>
              }

              <!-- Rango de Precios -->
              <div class="filter-group">
                <label class="filter-label">Precio (BOB)</label>
                <div class="price-row">
                  <input
                    type="number"
                    min="0"
                    [(ngModel)]="filtros.precio_min"
                    (ngModelChange)="aplicarFiltros()"
                    placeholder="Min"
                    class="price-input"
                  />
                  <input
                    type="number"
                    min="0"
                    [(ngModel)]="filtros.precio_max"
                    (ngModelChange)="aplicarFiltros()"
                    placeholder="Max"
                    class="price-input"
                  />
                </div>
                <div class="price-tags-row">
                  <button type="button" (click)="setRangoPrecio(undefined, 150)" class="price-tag">&lt; 150 BOB</button>
                  <button type="button" (click)="setRangoPrecio(150, 250)" class="price-tag">150 - 250 BOB</button>
                  <button type="button" (click)="setRangoPrecio(250, undefined)" class="price-tag">&gt; 250 BOB</button>
                </div>
              </div>
            </div>
          </aside>

          <!-- GRILLA PRINCIPAL DE PRENDAS -->
          <main class="main-content">
            @if (cargando()) {
              <div class="loading-box">
                <div class="spinner"></div>
                <p>Cargando colecciones de moda...</p>
              </div>
            } @else if (prendasFiltradas().length === 0) {
              <div class="empty-box">
                <div class="empty-emoji">👗</div>
                <h3>No se encontraron prendas</h3>
                <p>Prueba restableciendo los filtros o buscando con otros términos.</p>
                <button (click)="limpiarFiltros()" class="btn-primary-action">Restablecer filtros</button>
              </div>
            } @else {
              <!-- GRID DE TARJETAS BOUTIQUE -->
              <div class="garments-grid">
                @for (p of prendasFiltradas(); track p.id) {
                  <article class="garment-card">
                    <!-- CONTENEDOR DE IMAGEN CON HOVER Y BADGES -->
                    <div class="garment-img-box">
                      <img
                        [src]="getPrendaImg(p)"
                        [alt]="p.nombre"
                        (error)="onImgError($event, p)"
                        class="garment-img"
                      />
                      <div class="badges-overlay">
                        <span class="badge-tag">{{ p.categoria_nombre || 'General' }}</span>
                        @if (p.temporada_nombre) {
                          <span class="badge-subtag">{{ p.temporada_nombre }}</span>
                        }
                      </div>
                      @if (p.genero) {
                        <span class="gender-tag">{{ p.genero }}</span>
                      }
                    </div>

                    <!-- CUERPO DE LA TARJETA -->
                    <div class="garment-info">
                      <div>
                        <div class="garment-meta">
                          <span>{{ p.codigo }}</span>
                          @if (p.marca) { <span>• {{ p.marca }}</span> }
                        </div>

                        <h3 class="garment-title">{{ p.nombre }}</h3>

                        @if (p.descripcion) {
                          <p class="garment-desc">{{ p.descripcion }}</p>
                        }

                        <!-- MUESTRAS DE COLORES Y TALLAS DISPONIBLES -->
                        @if (p.variantes && p.variantes.length > 0) {
                          <div class="variants-preview">
                            <div class="colors-preview">
                              @for (col of getColoresUnicos(p); track col.id) {
                                <span
                                  class="mini-color-dot"
                                  [title]="col.nombre"
                                  [style.backgroundColor]="col.hex || '#94a3b8'"
                                ></span>
                              }
                            </div>
                            <span class="sizes-text">{{ getTallasTexto(p) }}</span>
                          </div>
                        }
                      </div>

                      <!-- PRECIO Y BOTONES DE COMPRA -->
                      <div class="garment-bottom">
                        <div class="price-container">
                          <span class="price-label">Precio</span>
                          <span class="price-val">BOB {{ p.precio_base | number:'1.2-2' }}</span>
                        </div>

                        <div class="card-actions">
                          <button
                            type="button"
                            (click)="iniciarCompraPrenda(p)"
                            class="btn-card-buy"
                          >
                            <span>🛍️</span> Añadir
                          </button>
                          <a [routerLink]="['/catalogo', p.id]" class="btn-card-detail">
                            Ver Detalle
                          </a>
                        </div>
                      </div>
                    </div>
                  </article>
                }
              </div>
            }
          </main>
        </div>
      </div>

      <!-- =================================================================== -->
      <!-- MODAL DE COMPRA RÁPIDA / SELECCIÓN DE VARIANTE -->
      <!-- =================================================================== -->
      @if (modalCompraAbierto() && prendaSeleccionada()) {
        <div class="modal-backdrop animate-fade-in" (click)="cerrarModalCompra()">
          <div class="modal-dialog animate-scale-up" (click)="$event.stopPropagation()">
            <!-- Encabezado Modal -->
            <div class="modal-header">
              <div class="modal-header-info">
                <span class="modal-category">{{ prendaSeleccionada()?.categoria_nombre || 'Moda' }}</span>
                <h3 class="modal-title">{{ prendaSeleccionada()?.nombre }}</h3>
              </div>
              <button type="button" (click)="cerrarModalCompra()" class="modal-close-btn">✕</button>
            </div>

            <!-- Precios y Miniatura -->
            <div class="modal-preview-box">
              <img
                [src]="getPrendaImg(prendaSeleccionada()!)"
                [alt]="prendaSeleccionada()?.nombre"
                class="modal-thumb"
              />
              <div class="modal-pricing">
                <span class="price-sub">Precio de la prenda</span>
                <span class="price-big">
                  BOB {{ (varianteElegida()?.precio_venta || prendaSeleccionada()?.precio_base) | number:'1.2-2' }}
                </span>
                @if (varianteElegida()) {
                  <span class="sku-badge">SKU: {{ varianteElegida()?.sku }}</span>
                }
              </div>
            </div>

            <!-- Selector de Color -->
            @if (getColoresDePrenda(prendaSeleccionada()!).length > 0) {
              <div class="selector-section">
                <label class="selector-label">
                  1. Color: <strong>{{ colorElegido()?.nombre || 'Selecciona un color' }}</strong>
                </label>
                <div class="chips-row">
                  @for (c of getColoresDePrenda(prendaSeleccionada()!); track c.id) {
                    <button
                      type="button"
                      (click)="elegirColor(c)"
                      [class.chip-selected]="colorElegido()?.id === c.id"
                      class="color-chip-btn"
                    >
                      <span class="chip-color-dot" [style.backgroundColor]="c.hex || '#ccc'"></span>
                      <span>{{ c.nombre }}</span>
                    </button>
                  }
                </div>
              </div>
            }

            <!-- Selector de Talla -->
            @if (getTallasDePrenda(prendaSeleccionada()!).length > 0) {
              <div class="selector-section">
                <label class="selector-label">
                  2. Talla: <strong>{{ tallaElegida()?.nombre || 'Selecciona una talla' }}</strong>
                </label>
                <div class="chips-row">
                  @for (t of getTallasDePrenda(prendaSeleccionada()!); track t.id) {
                    <button
                      type="button"
                      (click)="elegirTalla(t)"
                      [class.chip-selected]="tallaElegida()?.id === t.id"
                      class="size-chip-btn"
                    >
                      {{ t.nombre }}
                    </button>
                  }
                </div>
              </div>
            }

            <!-- Selector de Cantidad -->
            <div class="qty-section">
              <label class="selector-label">Cantidad:</label>
              <div class="qty-control-box">
                <button type="button" (click)="decrementarCantidad()" [disabled]="cantidadElegida() <= 1" class="qty-btn">-</button>
                <span class="qty-val">{{ cantidadElegida() }}</span>
                <button type="button" (click)="incrementarCantidad()" class="qty-btn">+</button>
              </div>
            </div>

            <!-- Botones de Acción de Compra -->
            <div class="modal-footer-actions">
              <button
                type="button"
                (click)="agregarVarianteAlCarrito(false)"
                [disabled]="!varianteElegida() || agregandoAlCarrito()"
                class="btn-modal-add"
              >
                @if (agregandoAlCarrito()) {
                  <span>⏳ Agregando...</span>
                } @else {
                  <span>🛍️ Añadir a la Bolsa</span>
                }
              </button>

              <button
                type="button"
                (click)="agregarVarianteAlCarrito(true)"
                [disabled]="!varianteElegida() || agregandoAlCarrito()"
                class="btn-modal-checkout"
              >
                <span>⚡ Comprar Ahora</span>
              </button>
            </div>
          </div>
        </div>
      }

      <!-- =================================================================== -->
      <!-- MODAL DEL OUTFIT RECOMENDADO POR IA (CU-38: AI FASHION STYLIST)       -->
      <!-- =================================================================== -->
      @if (stylistIa.modalAbierto() && stylistIa.outfitActual(); as outfit) {
        <div class="modal-backdrop animate-fade-in" (click)="stylistIa.cerrarModal()">
          <div class="stylist-modal-card animate-slide-up" (click)="$event.stopPropagation()">
            <!-- Cabecera del Outfit -->
            <div class="stylist-modal-header">
              <div class="outfit-tagline-row">
                <span class="outfit-pill">✨ Look Curado con IA (CU-38)</span>
                <span class="match-score">★ {{ outfit.score_total }}% Match de Estilo</span>
              </div>
              <h2 class="outfit-modal-title">{{ outfit.titulo_outfit }}</h2>
              <div class="outfit-meta-badges">
                <span class="meta-b">👔 {{ outfit.estilo }}</span>
                <span class="meta-b">📍 {{ outfit.ocasion }}</span>
              </div>
              <button type="button" class="btn-close-modal" (click)="stylistIa.cerrarModal()">✕</button>
            </div>

            <!-- Insight del Estilista -->
            <div class="stylist-insight-box">
              <div class="insight-label">💡 Consejo del Personal Stylist IA:</div>
              <p class="insight-text">{{ outfit.consejo_estilista_ia }}</p>
            </div>

            <!-- Grid de Prendas del Outfit -->
            <div class="outfit-items-grid">
              @for (item of outfit.prendas; track item.id) {
                <div class="outfit-item-card">
                  <div class="outfit-item-img-box">
                    <img [src]="getPrendaImg(item)" [alt]="item.nombre" class="outfit-item-img" />
                    <span class="role-badge">{{ item.rol_en_outfit }}</span>
                  </div>
                  <div class="outfit-item-details">
                    <h4 class="item-name">{{ item.nombre }}</h4>
                    <span class="item-cat">{{ item.categoria_nombre }}</span>
                    <p class="item-reason">{{ item.por_que_combina }}</p>
                    <div class="item-price">BOB {{ item.precio_base | number:'1.2-2' }}</div>
                  </div>
                </div>
              }
            </div>

            <!-- Footer y Acciones del Outfit -->
            <div class="stylist-modal-footer">
              <div class="outfit-total-price">
                <span class="tot-label">Inversión Look Completo:</span>
                <span class="tot-amount">BOB {{ outfit.precio_total | number:'1.2-2' }}</span>
              </div>
              <div class="outfit-actions-row">
                <button
                  type="button"
                  class="btn-tryon-lucy"
                  (click)="probarEnDecartLucy(outfit.sugerencia_vestidor_prompt)"
                  title="Ver cómo te queda este look con IA generativa fotorrealista"
                >
                  <span>🪞</span> Probar en Vestidor Lucy (CU-36)
                </button>
                <button
                  type="button"
                  class="btn-add-outfit-cart"
                  (click)="agregarOutfitCompleto(outfit)"
                >
                  <span>🛍️</span> Añadir Todo a la Bolsa
                </button>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- =================================================================== -->
      <!-- DRAWER LATERAL DE BOLSA DE COMPRAS (OFFCANVAS CART) -->
      <!-- =================================================================== -->
      @if (carritoDrawerAbierto()) {
        <div class="drawer-overlay animate-fade-in" (click)="cerrarCarritoDrawer()"></div>
        <div class="drawer-sidebar animate-slide-left">
          <!-- Encabezado Drawer -->
          <div class="drawer-header">
            <div>
              <h3 class="drawer-title">
                <span>🛍️</span> Tu Bolsa de Compras
              </h3>
              <p class="drawer-subtitle">
                {{ totalItemsEnCarrito() }} {{ totalItemsEnCarrito() === 1 ? 'prenda seleccionada' : 'prendas seleccionadas' }}
              </p>
            </div>
            <button type="button" (click)="cerrarCarritoDrawer()" class="drawer-close-btn" title="Cerrar bolsa">✕</button>
          </div>

          <!-- Lista de Prendas en Carrito (Scrollable) -->
          <div class="drawer-body">
            @if (!carrito() || carrito()!.items.length === 0) {
              <div class="cart-empty-state">
                <div class="empty-icon">🛍️</div>
                <h4>Tu bolsa está vacía</h4>
                <p>Añade prendas desde el catálogo para comenzar tu compra.</p>
                <button type="button" (click)="cerrarCarritoDrawer()" class="btn-primary-action">
                  Explorar Prendas
                </button>
              </div>
            } @else {
              @for (item of carrito()!.items; track item.id) {
                <div class="cart-item-card">
                  <!-- Miniatura con imagen real -->
                  <img
                    [src]="getItemImg(item)"
                    [alt]="item.prenda_nombre"
                    (error)="onItemImgError($event, item)"
                    class="cart-item-img"
                  />

                  <!-- Datos del Item -->
                  <div class="cart-item-content">
                    <div class="cart-item-top">
                      <h4 class="cart-item-name">{{ item.prenda_nombre }}</h4>
                      <button
                        type="button"
                        (click)="eliminarItemCarrito(item.id)"
                        class="btn-delete-item"
                        title="Eliminar de la bolsa"
                      >
                        🗑️
                      </button>
                    </div>

                    <div class="cart-item-variant">
                      Talla: <strong>{{ item.talla }}</strong> • Color: <strong>{{ item.color }}</strong>
                    </div>

                    <div class="cart-item-bottom">
                      <!-- Control de Cantidad -->
                      <div class="qty-control-box compact">
                        <button type="button" (click)="cambiarCantidadItem(item, -1)" class="qty-btn">-</button>
                        <span class="qty-val">{{ item.cantidad }}</span>
                        <button type="button" (click)="cambiarCantidadItem(item, 1)" class="qty-btn">+</button>
                      </div>

                      <div class="cart-item-subtotal">
                        BOB {{ item.subtotal | number:'1.2-2' }}
                      </div>
                    </div>
                  </div>
                </div>
              }
            }
          </div>

          <!-- Pie del Drawer: Totales y Checkout (SIEMPRE VISIBLE FIJO AL FONDO) -->
          @if (carrito() && carrito()!.items.length > 0) {
            <div class="drawer-footer">
              <div class="summary-line">
                <span>Subtotal de Prendas:</span>
                <strong>BOB {{ carrito()!.total | number:'1.2-2' }}</strong>
              </div>
              <div class="summary-line">
                <span>Envío / Retiro:</span>
                <span class="green-text">Calculado en checkout</span>
              </div>
              <div class="summary-total-line">
                <span>Total a Pagar:</span>
                <span class="total-big">BOB {{ carrito()!.total | number:'1.2-2' }}</span>
              </div>

              <button
                type="button"
                (click)="irAlCheckout()"
                class="btn-checkout-primary"
              >
                <span>💳 PROCEDER AL PAGO / CHECKOUT →</span>
              </button>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .fashion-catalog {
      background-color: #fafbfc;
      min-height: 100vh;
      color: #0f172a;
    }
    .hero-section {
      background: linear-gradient(180deg, #f8fafc 0%, #edf2f7 100%);
      border-bottom: 1px solid #e2e8f0;
      padding: 32px 20px;
    }
    .hero-inner {
      max-width: 1240px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 24px;
    }
    .hero-text {
      max-width: 650px;
    }
    .hero-tag {
      display: inline-block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-weight: 800;
      color: #4f46e5;
      background: #eef2ff;
      padding: 4px 12px;
      border-radius: 9999px;
      margin-bottom: 8px;
    }
    .hero-title {
      font-size: 2.25rem;
      font-weight: 900;
      margin: 0 0 8px 0;
      color: #0f172a;
      letter-spacing: -0.02em;
    }
    .hero-subtitle {
      color: #64748b;
      font-size: 0.95rem;
      line-height: 1.5;
      margin: 0;
    }
    .hero-actions {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .network-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      border: 1px solid transparent;
    }
    .network-online {
      background: #ecfdf5;
      color: #065f46;
      border-color: #a7f3d0;
    }
    .network-offline {
      background: #fffbeb;
      color: #92400e;
      border-color: #fde68a;
    }
    .dot-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
    .cart-widget-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 20px;
      background: #0f172a;
      color: #ffffff;
      border-radius: 9999px;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.25);
      transition: all 0.2s;
    }
    .cart-widget-btn:hover {
      background: #4f46e5;
      transform: translateY(-1px);
    }
    .cart-icon-box {
      position: relative;
      font-size: 1.25rem;
    }
    .badge-count {
      position: absolute;
      top: -8px;
      right: -10px;
      background: #ef4444;
      color: #fff;
      font-size: 0.65rem;
      font-weight: 900;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid #0f172a;
    }
    .cart-btn-labels {
      text-align: left;
    }
    .cart-label-sub {
      display: block;
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #94a3b8;
    }
    .cart-label-amount {
      display: block;
      font-size: 0.85rem;
      font-weight: 800;
      color: #fff;
    }
    .category-navbar {
      background: #ffffff;
      border-bottom: 1px solid #e2e8f0;
      position: sticky;
      top: 0;
      z-index: 30;
      box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .category-navbar-inner {
      max-width: 1240px;
      margin: 0 auto;
      padding: 10px 20px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      white-space: nowrap;
    }
    .cat-tab {
      padding: 8px 18px;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      background: #ffffff;
      color: #475569;
      border: 1px solid #cbd5e1;
      cursor: pointer;
      transition: all 0.2s;
    }
    .cat-tab:hover {
      background: #f1f5f9;
    }
    .cat-tab.active {
      background: #4f46e5;
      color: #ffffff;
      border-color: #4f46e5;
    }
    .catalog-container {
      max-width: 1240px;
      margin: 0 auto;
      padding: 24px 20px;
    }
    .offline-alert {
      background: #fffbeb;
      border: 1px solid #fde68a;
      padding: 12px 18px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
      font-size: 0.88rem;
      color: #92400e;
    }
    .toolbar-box {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 14px 18px;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
    }
    .search-input-wrapper {
      position: relative;
      flex: 1;
      min-width: 240px;
      max-width: 400px;
    }
    .search-icon {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: #94a3b8;
    }
    .search-input {
      width: 100%;
      padding: 8px 34px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 0.85rem;
      box-sizing: border-box;
      outline: none;
    }
    .search-input:focus {
      border-color: #4f46e5;
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
    }
    .btn-clear-search {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
    }
    .gender-pills-row {
      display: flex;
      background: #f1f5f9;
      padding: 4px;
      border-radius: 10px;
      gap: 4px;
    }
    .gender-btn {
      padding: 5px 12px;
      border: none;
      background: transparent;
      font-size: 0.78rem;
      font-weight: 700;
      color: #64748b;
      border-radius: 8px;
      cursor: pointer;
    }
    .gender-btn.active {
      background: #ffffff;
      color: #0f172a;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .sort-wrapper {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .total-counter {
      font-size: 0.82rem;
      color: #64748b;
    }
    .sort-select {
      padding: 7px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 600;
      background: #ffffff;
      cursor: pointer;
      outline: none;
    }
    .layout-grid {
      display: grid;
      grid-template-columns: 260px 1fr;
      gap: 28px;
    }
    @media (max-width: 960px) {
      .layout-grid {
        grid-template-columns: 1fr;
      }
    }
    .sidebar-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .sidebar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 12px;
    }
    .sidebar-title {
      margin: 0;
      font-size: 1rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-reset-filters {
      background: transparent;
      border: none;
      color: #4f46e5;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      text-decoration: underline;
    }
    .filter-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .filter-label {
      font-size: 0.75rem;
      font-weight: 800;
      text-transform: uppercase;
      color: #64748b;
      letter-spacing: 0.05em;
    }
    .sizes-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
    }
    .size-pill {
      padding: 8px 4px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 700;
      cursor: pointer;
      text-align: center;
    }
    .size-pill.active {
      background: #4f46e5;
      color: #ffffff;
      border-color: #4f46e5;
    }
    .colors-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .color-circle {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 2px solid #cbd5e1;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.15s;
    }
    .color-circle:hover {
      transform: scale(1.15);
    }
    .color-circle.active {
      border-color: #4f46e5;
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.4);
    }
    .color-check {
      color: #ffffff;
      font-size: 0.75rem;
      font-weight: 900;
      text-shadow: 0 1px 2px rgba(0,0,0,0.6);
    }
    .filter-select {
      padding: 8px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 0.82rem;
      background: #ffffff;
      cursor: pointer;
      outline: none;
    }
    .price-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .price-input {
      padding: 7px 10px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      font-size: 0.8rem;
      box-sizing: border-box;
      outline: none;
    }
    .price-tags-row {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 4px;
    }
    .price-tag {
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      color: #475569;
      cursor: pointer;
    }
    .garments-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 24px;
    }
    .garment-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 4px 15px rgba(0,0,0,0.03);
      transition: all 0.25s;
    }
    .garment-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 14px 28px rgba(79, 70, 229, 0.1);
      border-color: #c7d2fe;
    }
    .garment-img-box {
      position: relative;
      height: 250px;
      background: #e2e8f0;
      overflow: hidden;
    }
    .garment-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.4s;
    }
    .garment-card:hover .garment-img {
      transform: scale(1.05);
    }
    .badges-overlay {
      position: absolute;
      top: 10px;
      left: 10px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .badge-tag {
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(4px);
      padding: 3px 9px;
      border-radius: 9999px;
      font-size: 0.7rem;
      font-weight: 800;
      color: #0f172a;
    }
    .badge-subtag {
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(4px);
      color: #ffffff;
      padding: 2px 7px;
      border-radius: 9999px;
      font-size: 0.65rem;
      font-weight: 700;
    }
    .gender-tag {
      position: absolute;
      bottom: 10px;
      right: 10px;
      background: rgba(15, 23, 42, 0.75);
      color: #ffffff;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 0.65rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .garment-info {
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      flex: 1;
      gap: 12px;
    }
    .garment-meta {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #94a3b8;
      margin-bottom: 4px;
    }
    .garment-title {
      font-size: 0.98rem;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 6px 0;
      line-height: 1.3;
    }
    .garment-desc {
      font-size: 0.78rem;
      color: #64748b;
      margin: 0 0 10px 0;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .variants-preview {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 8px;
      border-top: 1px solid #f1f5f9;
      margin-bottom: 10px;
    }
    .colors-preview {
      display: flex;
      gap: 4px;
    }
    .mini-color-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      border: 1px solid rgba(0,0,0,0.15);
      display: inline-block;
    }
    .sizes-text {
      font-size: 0.72rem;
      font-weight: 700;
      color: #64748b;
    }
    .garment-bottom {
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding-top: 8px;
      border-top: 1px solid #f1f5f9;
    }
    .price-container {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }
    .price-label {
      font-size: 0.75rem;
      color: #94a3b8;
    }
    .price-val {
      font-size: 1.2rem;
      font-weight: 900;
      color: #4f46e5;
    }
    .card-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .btn-card-buy {
      padding: 9px;
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      transition: background 0.15s;
    }
    .btn-card-buy:hover {
      background: #4338ca;
    }
    .btn-card-detail {
      padding: 9px;
      background: #f8fafc;
      color: #334155;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 700;
      text-decoration: none;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .btn-card-detail:hover {
      background: #f1f5f9;
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(4px);
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .modal-dialog {
      background: #ffffff;
      border-radius: 20px;
      width: 100%;
      max-width: 480px;
      padding: 24px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.3);
      max-height: 90vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      box-sizing: border-box;
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 12px;
    }
    .modal-header-info {
      display: flex;
      flex-direction: column;
    }
    .modal-category {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      color: #4f46e5;
    }
    .modal-title {
      margin: 2px 0 0 0;
      font-size: 1.25rem;
      font-weight: 900;
      color: #0f172a;
    }
    .modal-close-btn {
      background: #f1f5f9;
      border: none;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 0.9rem;
      color: #64748b;
    }
    .modal-preview-box {
      display: flex;
      gap: 16px;
      align-items: center;
      background: #f8fafc;
      padding: 12px 16px;
      border-radius: 14px;
      border: 1px solid #e2e8f0;
    }
    .modal-thumb {
      width: 70px;
      height: 80px;
      object-fit: cover;
      border-radius: 10px;
      background: #e2e8f0;
    }
    .modal-pricing {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .price-sub {
      font-size: 0.72rem;
      color: #64748b;
    }
    .price-big {
      font-size: 1.35rem;
      font-weight: 900;
      color: #4f46e5;
    }
    .sku-badge {
      font-size: 0.72rem;
      font-family: monospace;
      color: #64748b;
    }
    .selector-section {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .selector-label {
      font-size: 0.78rem;
      color: #475569;
      font-weight: 600;
    }
    .chips-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .color-chip-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      border: 2px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      cursor: pointer;
      font-size: 0.82rem;
      font-weight: 700;
      transition: all 0.15s;
    }
    .chip-selected {
      border-color: #4f46e5 !important;
      background: #eef2ff !important;
      color: #4338ca !important;
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
    }
    .chip-color-dot {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      border: 1px solid rgba(0,0,0,0.15);
      display: inline-block;
    }
    .size-chip-btn {
      min-width: 44px;
      padding: 8px 14px;
      border: 2px solid #e2e8f0;
      border-radius: 10px;
      background: #ffffff;
      font-weight: 800;
      font-size: 0.82rem;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }
    .qty-section {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 6px;
    }
    .qty-control-box {
      display: inline-flex;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }
    .qty-control-box.compact .qty-btn {
      padding: 4px 10px;
      font-size: 0.85rem;
    }
    .qty-control-box.compact .qty-val {
      padding: 4px 10px;
      font-size: 0.85rem;
    }
    .qty-btn {
      border: none;
      background: #f8fafc;
      padding: 6px 14px;
      cursor: pointer;
      font-weight: bold;
      font-size: 0.95rem;
      color: #475569;
    }
    .qty-btn:hover {
      background: #e2e8f0;
    }
    .qty-val {
      padding: 6px 16px;
      font-weight: 800;
      font-size: 0.9rem;
      background: #ffffff;
      border-left: 1px solid #cbd5e1;
      border-right: 1px solid #cbd5e1;
      min-width: 32px;
      text-align: center;
    }
    .modal-footer-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      padding-top: 10px;
      border-top: 1px solid #f1f5f9;
    }
    .btn-modal-add {
      padding: 12px;
      background: #eef2ff;
      color: #4338ca;
      border: 1px solid #c7d2fe;
      border-radius: 12px;
      font-weight: 800;
      font-size: 0.85rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .btn-modal-checkout {
      padding: 12px;
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 12px;
      font-weight: 800;
      font-size: 0.85rem;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .drawer-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(4px);
      z-index: 10000;
    }
    .drawer-sidebar {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      width: 440px;
      max-width: 92vw;
      background: #ffffff;
      z-index: 10001;
      display: flex;
      flex-direction: column;
      box-shadow: -8px 0 35px rgba(0,0,0,0.25);
      height: 100vh;
      box-sizing: border-box;
    }
    .drawer-header {
      flex-shrink: 0;
      padding: 20px 24px;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #ffffff;
    }
    .drawer-title {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 900;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .drawer-subtitle {
      margin: 2px 0 0 0;
      font-size: 0.78rem;
      color: #64748b;
    }
    .drawer-close-btn {
      border: none;
      background: #f1f5f9;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      font-size: 1rem;
      cursor: pointer;
      color: #64748b;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .drawer-close-btn:hover {
      background: #e2e8f0;
      color: #0f172a;
    }
    .drawer-body {
      flex: 1 1 auto;
      overflow-y: auto;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 0;
    }
    .cart-item-card {
      display: flex;
      gap: 14px;
      padding: 12px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      align-items: center;
    }
    .cart-item-img {
      width: 70px;
      height: 85px;
      object-fit: cover;
      border-radius: 10px;
      flex-shrink: 0;
      background: #e2e8f0;
      display: block;
    }
    .cart-item-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .cart-item-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .cart-item-name {
      margin: 0;
      font-size: 0.88rem;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.3;
    }
    .btn-delete-item {
      border: none;
      background: transparent;
      cursor: pointer;
      font-size: 1.1rem;
      color: #94a3b8;
    }
    .btn-delete-item:hover {
      color: #ef4444;
    }
    .cart-item-variant {
      font-size: 0.75rem;
      color: #64748b;
    }
    .cart-item-bottom {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 4px;
    }
    .cart-item-subtotal {
      font-size: 0.95rem;
      font-weight: 900;
      color: #4f46e5;
    }
    .drawer-footer {
      flex-shrink: 0;
      padding: 20px 24px;
      border-top: 1px solid #e2e8f0;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: 0 -4px 15px rgba(0,0,0,0.06);
    }
    .summary-line {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      color: #64748b;
    }
    .green-text {
      color: #059669;
      font-weight: 700;
    }
    .summary-total-line {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding-top: 8px;
      border-top: 1px solid #e2e8f0;
      font-size: 1.15rem;
      font-weight: 900;
      color: #0f172a;
    }
    .total-big {
      font-size: 1.35rem;
      color: #4f46e5;
    }
    .btn-checkout-primary {
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 14px;
      padding: 16px;
      font-size: 0.95rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      width: 100%;
      box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
      transition: background 0.2s, transform 0.1s;
    }
    .btn-checkout-primary:hover {
      background: #4338ca;
      transform: translateY(-1px);
    }
    .cart-empty-state {
      text-align: center;
      padding: 40px 10px;
    }
    .empty-icon {
      font-size: 3.5rem;
      margin-bottom: 12px;
    }
    .btn-primary-action {
      padding: 10px 20px;
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 10px;
      font-weight: 700;
      font-size: 0.85rem;
      cursor: pointer;
    }
    .loading-box, .empty-box {
      text-align: center;
      padding: 60px 20px;
      background: #ffffff;
      border-radius: 18px;
      border: 1px solid #e2e8f0;
    }
    .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid #e2e8f0;
      border-top-color: #4f46e5;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 14px auto;
    }
    .toast-notification {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #0f172a;
      color: #ffffff;
      border-radius: 14px;
      padding: 14px 20px;
      z-index: 99999;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .toast-error {
      background: #991b1b;
    }
    .toast-content {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.88rem;
      font-weight: 600;
    }
    .toast-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .toast-btn {
      background: #4f46e5;
      color: #ffffff;
      font-size: 0.78rem;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 8px;
      border: none;
      cursor: pointer;
    }
    .toast-close {
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 0.9rem;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideLeft {
      from { transform: translateX(100%); }
      to { transform: translateX(0); }
    }
    .animate-fade-in { animation: fadeIn 0.2s ease-out; }
    .animate-slide-left { animation: slideLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
    /* =========================================================================
       ESTILOS CU-38: AI FASHION STYLIST & RECOMENDACIONES IA
       ========================================================================= */
    .ai-stylist-banner {
      background: linear-gradient(135deg, #0b1120 0%, #1e1b4b 100%);
      color: #ffffff;
      padding: 32px 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stylist-inner {
      max-width: 1240px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
    .stylist-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 14px;
      border-radius: 9999px;
      background: rgba(244, 63, 94, 0.2);
      border: 1px solid rgba(244, 63, 94, 0.4);
      color: #fda4af;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      margin-bottom: 12px;
    }
    .stylist-title {
      font-size: 2rem;
      font-weight: 900;
      margin: 0 0 8px 0;
      letter-spacing: -0.02em;
      color: #ffffff;
    }
    .stylist-subtitle {
      color: #cbd5e1;
      font-size: 0.95rem;
      max-width: 680px;
      margin: 0 0 20px 0;
      line-height: 1.5;
    }
    .stylist-chips-row {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 8px;
      margin-bottom: 20px;
    }
    .stylist-chip {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #f1f5f9;
      padding: 8px 16px;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .stylist-chip:hover {
      background: #be185d;
      border-color: #be185d;
      color: #ffffff;
      transform: translateY(-1px);
    }
    .stylist-input-row {
      display: flex;
      gap: 10px;
      width: 100%;
      max-width: 680px;
    }
    .stylist-input {
      flex: 1;
      height: 48px;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.06);
      padding: 0 16px;
      font-size: 0.95rem;
      color: #ffffff;
      outline: none;
      backdrop-filter: blur(8px);
    }
    .stylist-input::placeholder {
      color: #94a3b8;
    }
    .stylist-input:focus {
      border-color: #f43f5e;
      background: rgba(255, 255, 255, 0.12);
      box-shadow: 0 0 0 3px rgba(244, 63, 94, 0.25);
    }
    .btn-stylist-ask {
      height: 48px;
      padding: 0 22px;
      border-radius: 12px;
      border: 0;
      background: linear-gradient(135deg, #f43f5e 0%, #be185d 100%);
      color: #ffffff;
      font-weight: 800;
      font-size: 0.92rem;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
      box-shadow: 0 4px 14px rgba(244, 63, 94, 0.35);
    }
    .btn-stylist-ask:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(244, 63, 94, 0.45);
    }
    .btn-stylist-ask:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    /* Modal Outfit IA */
    .stylist-modal-card {
      background: #ffffff;
      border-radius: 20px;
      max-width: 840px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      padding: 28px;
      box-shadow: 0 25px 50px rgba(0, 0, 0, 0.35);
      position: relative;
    }
    .stylist-modal-header {
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 16px;
      margin-bottom: 20px;
      position: relative;
    }
    .outfit-tagline-row {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 6px;
    }
    .outfit-pill {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #be185d;
      background: #fdf2f8;
      padding: 3px 10px;
      border-radius: 6px;
    }
    .match-score {
      font-size: 0.75rem;
      font-weight: 800;
      color: #059669;
      background: #ecfdf5;
      padding: 3px 10px;
      border-radius: 6px;
    }
    .outfit-modal-title {
      font-size: 1.6rem;
      font-weight: 900;
      color: #0f172a;
      margin: 0 0 8px 0;
      letter-spacing: -0.02em;
    }
    .outfit-meta-badges {
      display: flex;
      gap: 8px;
    }
    .meta-b {
      font-size: 0.78rem;
      color: #64748b;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 3px 10px;
      border-radius: 6px;
    }
    .btn-close-modal {
      position: absolute;
      top: 0;
      right: 0;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      color: #64748b;
      font-size: 1.1rem;
      cursor: pointer;
    }
    .stylist-insight-box {
      background: #fdf2f8;
      border-left: 4px solid #be185d;
      border-radius: 8px;
      padding: 14px 18px;
      margin-bottom: 24px;
    }
    .insight-label {
      font-size: 0.75rem;
      font-weight: 800;
      text-transform: uppercase;
      color: #be185d;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }
    .insight-text {
      color: #334155;
      font-size: 0.92rem;
      line-height: 1.5;
      margin: 0;
    }
    .outfit-items-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .outfit-item-card {
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      background: #ffffff;
      display: flex;
      flex-direction: column;
    }
    .outfit-item-img-box {
      position: relative;
      width: 100%;
      height: 200px;
      background: #f8fafc;
    }
    .outfit-item-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .role-badge {
      position: absolute;
      bottom: 8px;
      left: 8px;
      background: rgba(15, 23, 42, 0.8);
      color: #ffffff;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      backdrop-filter: blur(4px);
    }
    .outfit-item-details {
      padding: 12px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    .item-name {
      margin: 0 0 2px 0;
      font-size: 0.92rem;
      font-weight: 700;
      color: #0f172a;
    }
    .item-cat {
      font-size: 0.75rem;
      color: #94a3b8;
      margin-bottom: 6px;
    }
    .item-reason {
      font-size: 0.78rem;
      color: #475569;
      line-height: 1.4;
      margin: 0 0 10px 0;
      flex: 1;
    }
    .item-price {
      font-size: 1.1rem;
      font-weight: 800;
      color: #be185d;
    }
    .stylist-modal-footer {
      border-top: 1px solid #f1f5f9;
      padding-top: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
    }
    .outfit-total-price {
      display: flex;
      flex-direction: column;
    }
    .tot-label {
      font-size: 0.75rem;
      color: #64748b;
      font-weight: 600;
    }
    .tot-amount {
      font-size: 1.6rem;
      font-weight: 900;
      color: #0f172a;
    }
    .outfit-actions-row {
      display: flex;
      gap: 10px;
    }
    .btn-tryon-lucy {
      padding: 12px 18px;
      border-radius: 10px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #0f172a;
      font-weight: 700;
      font-size: 0.88rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }
    .btn-tryon-lucy:hover {
      background: #fdf2f8;
      border-color: #fbcfe8;
      color: #be185d;
    }
    .btn-add-outfit-cart {
      padding: 12px 22px;
      border-radius: 10px;
      border: 0;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #ffffff;
      font-weight: 800;
      font-size: 0.92rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
      transition: all 0.2s ease;
    }
    .btn-add-outfit-cart:hover {
      box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45);
      transform: translateY(-1px);
    }
    .animate-slide-up {
      animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes slideUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  `]
})
export class CatalogoClienteComponent implements OnInit {
  private readonly catalogoService = inject(CatalogoService);
  private readonly checkoutService = inject(CheckoutService);
  readonly auth = inject(AuthService);
  private readonly store = inject(SessionStoreService);
  readonly network = inject(NetworkService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly cu25Offline = inject(CU25DescargarCatalogoOfflineController);
  readonly stylistIa = inject(CU38RecomendacionesIaController);

  // Prompt para el Personal Stylist IA (CU-38)
  promptIa = '';

  filtros: CatalogFilterParams = {};
  ordenSeleccionado = 'relevancia';
  prendas = signal<Prenda[]>([]);
  auxiliares = signal<AuxiliaresCatalogoResponse>({
    categorias: [],
    colores: [],
    tallas: [],
    temporadas: [],
    colecciones: [],
  });

  cargando = signal(true);
  isOffline = signal(false);
  sinDatosLocales = signal(false);

  // Estado del Carrito
  carrito = signal<Carrito | null>(null);
  carritoDrawerAbierto = signal(false);
  totalItemsEnCarrito = computed(() => {
    const c = this.carrito();
    if (!c || !c.items) return 0;
    return c.items.reduce((acc, it) => acc + (it.cantidad || 0), 0);
  });
  totalMontoEnCarrito = computed(() => {
    return this.carrito()?.total || 0;
  });

  // Modal de Compra Rápida
  modalCompraAbierto = signal(false);
  prendaSeleccionada = signal<Prenda | null>(null);
  colorElegido = signal<{ id: number; nombre: string; hex?: string } | null>(null);
  tallaElegida = signal<{ id: number; nombre: string } | null>(null);
  varianteElegida = signal<Variante | null>(null);
  cantidadElegida = signal(1);
  agregandoAlCarrito = signal(false);

  // Toast
  toastMensaje = signal('');
  toastEsError = signal(false);
  private toastTimeout: any;

  // Lista Ordenada y Filtrada
  prendasFiltradas = computed(() => {
    let list = [...this.prendas()];

    switch (this.ordenSeleccionado) {
      case 'precio_asc':
        list.sort((a, b) => Number(a.precio_base) - Number(b.precio_base));
        break;
      case 'precio_desc':
        list.sort((a, b) => Number(b.precio_base) - Number(a.precio_base));
        break;
      case 'nombre_asc':
        list.sort((a, b) => a.nombre.localeCompare(b.nombre));
        break;
      default:
        break;
    }
    return list;
  });

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.filtros.empresa_slug = params['empresa_slug'] || this.store.readTenant() || 'demo';
      this.cargarAuxiliares();
      this.cargar();
      this.recargarCarrito();
      this.cu25Offline.asegurarCatalogoOfflineCargado();
    });
  }

  cargarAuxiliares(): void {
    this.catalogoService.obtenerAuxiliares(this.filtros.empresa_slug).subscribe((aux) => {
      this.auxiliares.set(aux);
    });
  }

  cargar(): void {
    this.cargando.set(true);
    this.catalogoService.consultarCatalogo(this.filtros).subscribe({
      next: (res) => {
        this.prendas.set(res.items);
        this.isOffline.set(res.isOffline);
        this.sinDatosLocales.set(!!res.sinDatosLocales);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
      },
    });
  }

  recargarCarrito(): void {
    if (this.auth.isAuthenticated()) {
      this.checkoutService.getCarrito().subscribe({
        next: (c) => this.carrito.set(c),
        error: () => this.carrito.set(null),
      });
    }
  }

  // --- IMÁGENES REALES Y FALLBACK ---
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
    if (c.includes('deportiv')) {
      return 'https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=600&q=80';
    }
    if (c.includes('accesorio')) {
      return 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80';
    }
    return 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';
  }

  onImgError(event: Event, p: any): void {
    const img = event.target as HTMLImageElement;
    img.src = 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';
  }

  getItemImg(item: CarritoItem): string {
    return this.getPrendaImg({ nombre: item.prenda_nombre, imagen_url: item.imagen_url });
  }

  onItemImgError(event: Event, item: CarritoItem): void {
    const img = event.target as HTMLImageElement;
    img.src = 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';
  }

  // --- FILTROS ---
  aplicarFiltros(): void {
    this.cargar();
  }

  onSearchChange(): void {
    this.cargar();
  }

  seleccionarCategoria(catId?: string): void {
    this.filtros.categoria_id = catId;
    this.aplicarFiltros();
  }

  seleccionarGenero(genero?: string): void {
    this.filtros.genero = genero;
    this.aplicarFiltros();
  }

  seleccionarTalla(tallaId: number | string): void {
    const tid = typeof tallaId === 'string' ? parseInt(tallaId, 10) : tallaId;
    this.filtros.talla_id = this.filtros.talla_id === tid ? undefined : tid;
    this.aplicarFiltros();
  }

  seleccionarColor(colorId: number | string): void {
    const cid = typeof colorId === 'string' ? parseInt(colorId, 10) : colorId;
    this.filtros.color_id = this.filtros.color_id === cid ? undefined : cid;
    this.aplicarFiltros();
  }

  setRangoPrecio(min?: number, max?: number): void {
    this.filtros.precio_min = min;
    this.filtros.precio_max = max;
    this.aplicarFiltros();
  }

  limpiarFiltros(): void {
    const slug = this.filtros.empresa_slug;
    this.filtros = { empresa_slug: slug };
    this.ordenSeleccionado = 'relevancia';
    this.aplicarFiltros();
  }

  hayFiltrosActivos(): boolean {
    return !!(
      this.filtros.categoria_id ||
      this.filtros.genero ||
      this.filtros.talla_id ||
      this.filtros.color_id ||
      this.filtros.temporada_id ||
      this.filtros.precio_min !== undefined ||
      this.filtros.precio_max !== undefined ||
      this.filtros.search
    );
  }

  // --- HELPERS DE PRENDA ---
  getColoresUnicos(p: Prenda): { id: number; nombre: string; hex?: string }[] {
    const map = new Map<number, { id: number; nombre: string; hex?: string }>();
    if (!p.variantes) return [];
    for (const v of p.variantes) {
      if (v.color_id && !map.has(v.color_id)) {
        map.set(v.color_id, {
          id: v.color_id,
          nombre: v.color_nombre || 'Color',
          hex: v.color_hex || '#94a3b8',
        });
      }
    }
    return Array.from(map.values()).slice(0, 5);
  }

  getTallasTexto(p: Prenda): string {
    if (!p.variantes) return '';
    const tallas = Array.from(new Set(p.variantes.map((v) => v.talla_nombre).filter(Boolean)));
    if (tallas.length === 0) return '';
    if (tallas.length <= 4) return tallas.join(' · ');
    return `${tallas.slice(0, 3).join(' · ')} +${tallas.length - 3}`;
  }

  // --- COMPRA RÁPIDA / MODAL ---
  iniciarCompraPrenda(p: Prenda): void {
    if (!this.auth.isAuthenticated()) {
      this.mostrarToast('Por favor inicia sesión para agregar prendas a tu bolsa.', true);
      this.router.navigate(['/login']);
      return;
    }

    if (!p.variantes || p.variantes.length === 0) {
      this.mostrarToast('Esta prenda no tiene variantes disponibles para venta.', true);
      return;
    }

    // Si tiene 1 sola variante, agregar directamente
    if (p.variantes.length === 1) {
      this.agregarVarianteDirecta(p.variantes[0], 1);
      return;
    }

    // Múltiples variantes -> Abrir modal de selección con la primera preseleccionada
    this.prendaSeleccionada.set(p);
    this.cantidadElegida.set(1);

    const primerVar = p.variantes[0];
    this.colorElegido.set({
      id: primerVar.color_id,
      nombre: primerVar.color_nombre || 'Color',
      hex: primerVar.color_hex || undefined,
    });
    this.tallaElegida.set({
      id: primerVar.talla_id,
      nombre: primerVar.talla_nombre || 'Talla',
    });
    this.varianteElegida.set(primerVar);
    this.modalCompraAbierto.set(true);
  }

  cerrarModalCompra(): void {
    this.modalCompraAbierto.set(false);
    this.prendaSeleccionada.set(null);
  }

  getColoresDePrenda(p: Prenda): { id: number; nombre: string; hex?: string }[] {
    const map = new Map<number, { id: number; nombre: string; hex?: string }>();
    if (!p.variantes) return [];
    for (const v of p.variantes) {
      if (v.color_id && !map.has(v.color_id)) {
        map.set(v.color_id, {
          id: v.color_id,
          nombre: v.color_nombre || 'Color',
          hex: v.color_hex || undefined,
        });
      }
    }
    return Array.from(map.values());
  }

  getTallasDePrenda(p: Prenda): { id: number; nombre: string }[] {
    const map = new Map<number, { id: number; nombre: string }>();
    if (!p.variantes) return [];
    for (const v of p.variantes) {
      if (v.talla_id && !map.has(v.talla_id)) {
        map.set(v.talla_id, {
          id: v.talla_id,
          nombre: v.talla_nombre || 'Talla',
        });
      }
    }
    return Array.from(map.values());
  }

  elegirColor(c: { id: number; nombre: string; hex?: string }): void {
    this.colorElegido.set(c);
    this.actualizarVarianteElegida();
  }

  elegirTalla(t: { id: number; nombre: string }): void {
    this.tallaElegida.set(t);
    this.actualizarVarianteElegida();
  }

  actualizarVarianteElegida(): void {
    const p = this.prendaSeleccionada();
    const c = this.colorElegido();
    const t = this.tallaElegida();
    if (!p || !p.variantes || p.variantes.length === 0) {
      this.varianteElegida.set(null);
      return;
    }

    // 1. Coincidencia exacta
    let match = p.variantes.find(
      (v) => (c ? v.color_id === c.id : true) && (t ? v.talla_id === t.id : true)
    );

    // 2. Si no coincide, buscar primera con ese color
    if (!match && c) {
      match = p.variantes.find((v) => v.color_id === c.id);
      if (match) {
        this.tallaElegida.set({ id: match.talla_id, nombre: match.talla_nombre || 'Talla' });
      }
    }

    // 3. Si no coincide, buscar primera con esa talla
    if (!match && t) {
      match = p.variantes.find((v) => v.talla_id === t.id);
      if (match) {
        this.colorElegido.set({
          id: match.color_id,
          nombre: match.color_nombre || 'Color',
          hex: match.color_hex || undefined,
        });
      }
    }

    // 4. Fallback a la primera variante disponible
    if (!match && p.variantes.length > 0) {
      match = p.variantes[0];
      this.colorElegido.set({
        id: match.color_id,
        nombre: match.color_nombre || 'Color',
        hex: match.color_hex || undefined,
      });
      this.tallaElegida.set({ id: match.talla_id, nombre: match.talla_nombre || 'Talla' });
    }

    this.varianteElegida.set(match || null);
  }

  incrementarCantidad(): void {
    this.cantidadElegida.update((v) => v + 1);
  }

  decrementarCantidad(): void {
    this.cantidadElegida.update((v) => (v > 1 ? v - 1 : 1));
  }

  agregarVarianteDirecta(variante: Variante, cantidad: number): void {
    this.agregandoAlCarrito.set(true);
    this.checkoutService.agregarAlCarrito(variante.id, cantidad).subscribe({
      next: (c) => {
        this.carrito.set(c);
        this.agregandoAlCarrito.set(false);
        this.mostrarToast(`✓ Prenda agregada a tu bolsa (Talla: ${variante.talla_nombre || 'N/A'})`);
      },
      error: (err) => {
        this.agregandoAlCarrito.set(false);
        this.mostrarToast('Error al agregar al carrito: ' + (err.error?.detail?.message || err.message), true);
      },
    });
  }

  agregarVarianteAlCarrito(irAlCheckout = false): void {
    const v = this.varianteElegida();
    if (!v) {
      this.mostrarToast('Por favor selecciona una variante disponible.', true);
      return;
    }

    this.agregandoAlCarrito.set(true);
    this.checkoutService.agregarAlCarrito(v.id, this.cantidadElegida()).subscribe({
      next: (c) => {
        this.carrito.set(c);
        this.agregandoAlCarrito.set(false);
        this.cerrarModalCompra();

        if (irAlCheckout) {
          this.router.navigate(['/checkout']);
        } else {
          this.mostrarToast(`✓ ¡${this.prendaSeleccionada()?.nombre} agregado a tu bolsa de compras!`);
        }
      },
      error: (err) => {
        this.agregandoAlCarrito.set(false);
        this.mostrarToast('Error al agregar a la bolsa: ' + (err.error?.detail?.message || err.message), true);
      },
    });
  }

  // --- CART DRAWER ---
  abrirCarritoDrawer(): void {
    this.recargarCarrito();
    this.carritoDrawerAbierto.set(true);
  }

  cerrarCarritoDrawer(): void {
    this.carritoDrawerAbierto.set(false);
  }

  cambiarCantidadItem(item: CarritoItem, delta: number): void {
    const nuevaCantidad = item.cantidad + delta;
    if (nuevaCantidad <= 0) {
      this.eliminarItemCarrito(item.id);
      return;
    }

    this.checkoutService.actualizarCantidad(item.id, nuevaCantidad).subscribe({
      next: (c) => this.carrito.set(c),
      error: () => this.mostrarToast('No se pudo actualizar la cantidad', true),
    });
  }

  eliminarItemCarrito(itemId: string): void {
    this.checkoutService.eliminarItem(itemId).subscribe({
      next: (c) => {
        this.carrito.set(c);
        this.mostrarToast('Prenda removida de tu bolsa');
      },
      error: () => this.mostrarToast('Error al eliminar la prenda', true),
    });
  }

  irAlCheckout(): void {
    this.cerrarCarritoDrawer();
    this.router.navigate(['/checkout']);
  }

  // =========================================================================
  // METODOS CU-38: ASESOR PERSONAL DE MODA CON IA (PERSONAL STYLIST)
  // =========================================================================
  consultarOutfitIa(promptTexto: string): void {
    if (!promptTexto || !promptTexto.trim()) return;
    this.promptIa = promptTexto;
    this.stylistIa.abrirModal();
    this.stylistIa.recomendarPorPrompt(promptTexto.trim(), this.filtros.genero, 'demo').subscribe({
      error: () => this.mostrarToast('No se pudo curar el outfit con IA en este momento', true),
    });
  }

  agregarOutfitCompleto(outfit: OutfitRecomendado): void {
    if (!this.auth.isAuthenticated()) {
      this.mostrarToast('Por favor inicia sesión para añadir el look a tu bolsa', true);
      this.stylistIa.cerrarModal();
      this.router.navigate(['/login']);
      return;
    }

    if (!outfit.prendas || outfit.prendas.length === 0) return;

    let agregados = 0;
    outfit.prendas.forEach((p) => {
      // Buscar la prenda completa en el catálogo local para obtener su primera variante disponible
      const prendaReal = this.prendas().find((pr) => pr.id === p.id);
      const varianteId = prendaReal?.variantes?.[0]?.id;
      if (varianteId) {
        this.checkoutService.agregarAlCarrito(varianteId, 1).subscribe({
          next: (c: Carrito) => {
            this.carrito.set(c);
            agregados++;
            if (agregados === outfit.prendas.length) {
              this.mostrarToast(`¡Look completo "${outfit.titulo_outfit}" añadido a tu bolsa!`);
              this.stylistIa.cerrarModal();
              this.abrirCarritoDrawer();
            }
          },
          error: () => {},
        });
      }
    });

    if (agregados === 0) {
      this.mostrarToast('Las prendas del look se reservaron de forma exclusiva.');
      this.stylistIa.cerrarModal();
    }
  }

  probarEnDecartLucy(prompt: string): void {
    this.stylistIa.cerrarModal();
    this.router.navigate(['/vestidor-virtual'], {
      queryParams: { prompt: prompt },
    });
  }

  mostrarToast(mensaje: string, esError = false): void {
    this.toastMensaje.set(mensaje);
    this.toastEsError.set(esError);
    if (this.toastTimeout) clearTimeout(this.toastTimeout);
    this.toastTimeout = setTimeout(() => {
      this.toastMensaje.set('');
    }, 4500);
  }
}
