import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';

import { CatalogoService, CatalogFilterParams } from '../../core/catalogo.service';
import { AuxiliaresCatalogoResponse, Prenda } from '../../core/models';
import { NetworkService } from '../../core/network.service';

@Component({
  selector: 'app-catalogo-cliente',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-6 max-w-7xl font-sans">
      <!-- HEADER TIENDA -->
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-gray-200 mb-6 gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight text-gray-900">Catalogo de Prendas</h1>
          <p class="text-sm text-gray-500 mt-1">
            Explora las colecciones y prendas disponibles de la tienda
          </p>
        </div>
        <div class="flex items-center gap-3">
          <span
            [class]="network.online() ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'"
            class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
          >
            <span [class]="network.online() ? 'bg-green-500' : 'bg-amber-500'" class="w-2 h-2 rounded-full"></span>
            {{ network.online() ? 'En linea' : 'Modo Desconectado' }}
          </span>
        </div>
      </div>

      <!-- BANNER OBLIGATORIO DE ADVERTENCIA OFFLINE (CU-13 / Seccion 5.3) -->
      @if (isOffline()) {
        <div class="mb-6 p-4 rounded-xl border-2 border-amber-300 bg-amber-50 shadow-sm flex items-start gap-3">
          <div class="text-amber-600 text-2xl leading-none">⚠️</div>
          <div>
            <h2 class="text-sm font-bold text-amber-900 uppercase tracking-wide">
              Modo sin conexion activo
            </h2>
            <p class="text-sm text-amber-800 mt-0.5">
              La informacion de catalogo y precios corresponde a la ultima descarga local y podria estar desactualizada.
            </p>
          </div>
        </div>
      }

      <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <!-- PANEL LATERAL DE FILTROS COMBINADOS (CU-14) -->
        <aside class="lg:col-span-1 bg-white p-5 rounded-2xl border border-gray-200 shadow-sm h-fit">
          <div class="flex justify-between items-center mb-4 pb-3 border-b border-gray-100">
            <h2 class="font-bold text-gray-900 text-base">Filtros</h2>
            <button
              (click)="limpiarFiltros()"
              class="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              Restablecer
            </button>
          </div>

          <!-- Buscador -->
          <div class="mb-4">
            <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Buscar</label>
            <input
              type="text"
              [(ngModel)]="filtros.search"
              (ngModelChange)="aplicarFiltros()"
              placeholder="Nombre, estilo o marca..."
              class="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <!-- Categoria -->
          <div class="mb-4">
            <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Categoria</label>
            <select
              [(ngModel)]="filtros.categoria_id"
              (ngModelChange)="aplicarFiltros()"
              class="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option [ngValue]="undefined">Todas las categorias</option>
              @for (cat of auxiliares().categorias; track cat.id) {
                <option [value]="cat.id">{{ cat.nombre }}</option>
              }
            </select>
          </div>

          <!-- Temporada -->
          <div class="mb-4">
            <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Temporada</label>
            <select
              [(ngModel)]="filtros.temporada_id"
              (ngModelChange)="aplicarFiltros()"
              class="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option [ngValue]="undefined">Todas las temporadas</option>
              @for (temp of auxiliares().temporadas; track temp.id) {
                <option [value]="temp.id">{{ temp.nombre }}</option>
              }
            </select>
          </div>

          <!-- Genero -->
          <div class="mb-4">
            <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Genero</label>
            <select
              [(ngModel)]="filtros.genero"
              (ngModelChange)="aplicarFiltros()"
              class="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option [ngValue]="undefined">Cualquier genero</option>
              <option value="mujer">Mujer</option>
              <option value="hombre">Hombre</option>
              <option value="nino">Niño</option>
              <option value="unisex">Unisex</option>
            </select>
          </div>

          <!-- Rango de precios -->
          <div class="mb-4">
            <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Precio (BOB)</label>
            <div class="grid grid-cols-2 gap-2">
              <input
                type="number"
                min="0"
                [(ngModel)]="filtros.precio_min"
                (ngModelChange)="aplicarFiltros()"
                placeholder="Min"
                class="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <input
                type="number"
                min="0"
                [(ngModel)]="filtros.precio_max"
                (ngModelChange)="aplicarFiltros()"
                placeholder="Max"
                class="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          <!-- Talla -->
          @if (auxiliares().tallas.length > 0) {
            <div class="mb-4">
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Talla</label>
              <div class="flex flex-wrap gap-1.5">
                @for (t of auxiliares().tallas; track t.id) {
                  <button
                    type="button"
                    (click)="seleccionarTalla(t.id)"
                    [class]="filtros.talla_id === t.id ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800 hover:bg-gray-200'"
                    class="px-2.5 py-1 rounded text-xs font-medium transition"
                  >
                    {{ t.nombre }}
                  </button>
                }
              </div>
            </div>
          }
        </aside>

        <!-- CONTENIDO PRINCIPAL: PRODUCTOS -->
        <main class="lg:col-span-3">
          @if (cargando()) {
            <div class="flex flex-col items-center justify-center p-12 text-gray-400">
              <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-3"></div>
              <p class="text-sm">Cargando catalogo...</p>
            </div>
          } @else if (sinDatosLocales()) {
            <!-- FLUJO ALTERNATIVO 5.a: Sin red y sin snapshot previo -->
            <div class="bg-gray-50 border border-gray-200 rounded-2xl p-12 text-center max-w-md mx-auto">
              <div class="text-4xl mb-3">📡</div>
              <h3 class="text-lg font-bold text-gray-900 mb-1">Sin datos locales disponibles</h3>
              <p class="text-sm text-gray-600 mb-6">
                Se requiere conectar al menos una vez con acceso a Internet para descargar y almacenar el catalogo de productos.
              </p>
              <button
                (click)="cargar()"
                class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition"
              >
                Reintentar conexion
              </button>
            </div>
          } @else if (prendas().length === 0) {
            <!-- FLUJO ALTERNATIVO 5.a CU-14: No hay coincidencias -->
            <div class="bg-white border border-gray-200 rounded-2xl p-12 text-center">
              <div class="text-4xl mb-3">🔍</div>
              <h3 class="text-base font-bold text-gray-900 mb-1">
                No se encontraron prendas con los criterios seleccionados
              </h3>
              <p class="text-sm text-gray-500 mb-4">
                Prueba relajando los filtros o buscando con otro termino.
              </p>
              <button
                (click)="limpiarFiltros()"
                class="px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-sm font-medium hover:bg-indigo-100 transition"
              >
                Restablecer todos los filtros
              </button>
            </div>
          } @else {
            <!-- GRILLA DE PRENDAS -->
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              @for (p of prendas(); track p.id) {
                <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col hover:shadow-md transition">
                  <div class="h-48 bg-gray-100 relative overflow-hidden flex items-center justify-center">
                    @if (p.imagen_url) {
                      <img [src]="p.imagen_url" [alt]="p.nombre" class="w-full h-full object-cover" />
                    } @else {
                      <span class="text-gray-400 text-sm">Sin imagen</span>
                    }
                    <span class="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded text-xs font-semibold text-gray-700 shadow-sm">
                      {{ p.categoria_nombre || 'General' }}
                    </span>
                  </div>
                  <div class="p-4 flex-1 flex flex-col justify-between">
                    <div>
                      <div class="text-xs text-gray-400 uppercase tracking-wider mb-1">
                        {{ p.codigo }} @if (p.marca) { • {{ p.marca }} }
                      </div>
                      <h3 class="font-bold text-gray-900 text-base leading-snug mb-1">
                        {{ p.nombre }}
                      </h3>
                      @if (p.descripcion) {
                        <p class="text-xs text-gray-500 line-clamp-2 mb-3">{{ p.descripcion }}</p>
                      }
                    </div>

                    <div class="pt-3 border-t border-gray-100">
                      <!-- Variantes badges -->
                      @if (p.variantes.length > 0) {
                        <div class="flex flex-wrap gap-1 mb-2">
                          @for (v of p.variantes.slice(0, 4); track v.id) {
                            <span class="inline-flex items-center gap-1 text-[11px] bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded">
                              @if (v.color_hex) {
                                <span class="w-2 h-2 rounded-full border border-gray-300" [style.backgroundColor]="v.color_hex"></span>
                              }
                              {{ v.talla_nombre || 'Talla' }}
                            </span>
                          }
                          @if (p.variantes.length > 4) {
                            <span class="text-[10px] text-gray-400 self-center">+{{ p.variantes.length - 4 }}</span>
                          }
                        </div>
                      }
                      <div class="flex items-baseline justify-between">
                        <span class="text-xs text-gray-400 font-medium">Desde</span>
                        <span class="text-lg font-black text-indigo-700">
                          BOB {{ p.precio_base }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              }
            </div>
          }
        </main>
      </div>
    </div>
  `,
})
export class CatalogoClienteComponent implements OnInit {
  private readonly catalogoService = inject(CatalogoService);
  readonly network = inject(NetworkService);
  private readonly route = inject(ActivatedRoute);

  filtros: CatalogFilterParams = {};
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

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      if (params['empresa_slug']) {
        this.filtros.empresa_slug = params['empresa_slug'];
      }
      this.cargarAuxiliares();
      this.cargar();
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

  aplicarFiltros(): void {
    this.cargar();
  }

  seleccionarTalla(tallaId: number | string): void {
    const tid = typeof tallaId === 'string' ? parseInt(tallaId, 10) : tallaId;
    if (this.filtros.talla_id === tid) {
      this.filtros.talla_id = undefined;
    } else {
      this.filtros.talla_id = tid;
    }
    this.aplicarFiltros();
  }

  limpiarFiltros(): void {
    const slug = this.filtros.empresa_slug;
    this.filtros = { empresa_slug: slug };
    this.aplicarFiltros();
  }
}

