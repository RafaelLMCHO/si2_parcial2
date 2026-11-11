import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';

@Component({
  selector: 'app-catalogo-offline',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-4xl font-sans">
      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-25: Catálogo Offline (IndexedDB / LocalStorage)</h1>
        <p class="text-sm text-gray-500">Descarga y persistencia del catálogo para operar en contingencia sin conexión</p>
      </div>

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div class="p-4 bg-indigo-50 border border-indigo-100 rounded-xl text-xs text-indigo-800">
          Almacena localmente prendas, variantes, existencias por sucursal y precios vigentes mediante compresión gzip.
        </div>

        @if (ctrl.ultimaDescarga(); as fecha) {
          <div class="text-xs text-gray-600">
            <strong>Última descarga:</strong> {{ fecha | date:'medium' }} • <strong>Prendas:</strong> {{ ctrl.articulosDescargados() }} • <strong>Sucursales:</strong> {{ ctrl.sucursalesDescargadas() }}
          </div>
        }

        @if (ctrl.error()) {
          <div class="p-3 bg-red-50 text-red-700 text-xs rounded-xl">{{ ctrl.error() }}</div>
        }

        <button
          (click)="descargar()"
          [disabled]="ctrl.cargando()"
          class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition disabled:opacity-50"
        >
          {{ ctrl.cargando() ? 'Descargando paquete optimizado...' : 'Actualizar Catálogo Offline Ahora' }}
        </button>
      </div>
    </div>
  `
})
export class CatalogoOfflineComponent {
  ctrl = inject(CU25DescargarCatalogoOfflineController);

  descargar() {
    this.ctrl.descargarCatalogo().subscribe();
  }
}

