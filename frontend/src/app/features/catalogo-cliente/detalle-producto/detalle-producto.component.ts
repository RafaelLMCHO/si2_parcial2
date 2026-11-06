import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CatalogoService } from '../../../core/catalogo.service';
import { Prenda, VariantePrenda } from '../../../core/models';

@Component({
  selector: 'app-detalle-producto',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-5xl font-sans">
      <div class="mb-4">
        <a routerLink="/catalogo" class="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
          ← Volver al catálogo
        </a>
      </div>

      @if (cargando()) {
        <div class="flex justify-center p-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
      } @else if (prenda(); as p) {
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 bg-white p-8 rounded-3xl border border-gray-100 shadow-sm">
          <div class="rounded-2xl overflow-hidden bg-gray-50 flex items-center justify-center min-h-[350px]">
            @if (p.imagen_url) {
              <img [src]="p.imagen_url" [alt]="p.nombre" class="w-full h-full object-cover" />
            } @else {
              <span class="text-gray-400">Sin imagen disponible</span>
            }
          </div>

          <div class="flex flex-col justify-between">
            <div>
              <div class="text-xs uppercase font-bold tracking-wider text-gray-400 mb-1">
                {{ p.codigo }} • {{ p.categoria_nombre || 'General' }}
              </div>
              <h1 class="text-2xl font-black text-gray-900 mb-2">{{ p.nombre }}</h1>
              <div class="text-2xl font-bold text-indigo-600 mb-4">BOB {{ p.precio_base }}</div>
              <p class="text-sm text-gray-600 mb-6 leading-relaxed">{{ p.descripcion || 'Sin descripción' }}</p>

              <div class="mb-6">
                <span class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Variantes (Talla / Color)</span>
                <div class="flex flex-wrap gap-2">
                  @for (v of p.variantes; track v.id) {
                    <button
                      (click)="seleccionarVariante(v)"
                      [class]="varianteSeleccionada()?.id === v.id ? 'border-indigo-600 bg-indigo-50 text-indigo-700' : 'border-gray-200 hover:bg-gray-50'"
                      class="px-3 py-1.5 border rounded-xl text-xs font-semibold flex items-center gap-2"
                    >
                      @if (v.color_hex) {
                        <span class="w-3 h-3 rounded-full border border-gray-300" [style.backgroundColor]="v.color_hex"></span>
                      }
                      <span>{{ v.talla_nombre || 'Talla' }}</span>
                    </button>
                  }
                </div>
              </div>
            </div>

            <div class="flex gap-3 pt-6 border-t">
              <button class="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition">
                Agregar al Carrito
              </button>
              <a [routerLink]="['/reservas']" class="px-5 py-3 border border-indigo-600 text-indigo-600 hover:bg-indigo-50 font-bold rounded-xl text-sm transition">
                Reservar Probador
              </a>
            </div>
          </div>
        </div>
      }
    </div>
  `
})
export class DetalleProductoComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private catalogoService = inject(CatalogoService);

  cargando = signal(false);
  prenda = signal<Prenda | null>(null);
  varianteSeleccionada = signal<VariantePrenda | null>(null);

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.cargar(id);
    }
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
      },
      error: () => this.cargando.set(false)
    });
  }

  seleccionarVariante(v: VariantePrenda) {
    this.varianteSeleccionada.set(v);
  }
}

