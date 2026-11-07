import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { CU30ColaOperacionesOfflineController } from '../../../controller/cu30_cola_operaciones_offline_controller';
import { CU31SincronizarOperacionesController } from '../../../controller/cu31_sincronizar_operaciones_controller';

@Component({
  selector: 'app-cola-operaciones',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-5xl font-sans">
      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-30 y CU-31: Cola Outbox y Sincronización</h1>
          <p class="text-sm text-gray-500">Monitoreo de ciclo de vida y sincronización por lotes con idempotencia (RNF05)</p>
        </div>
        <div class="flex gap-2">
          <button (click)="cargar()" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs font-semibold rounded-lg">
            Refrescar
          </button>
          <button
            (click)="sincronizar()"
            [disabled]="syncCtrl.cargando()"
            class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg disabled:opacity-50"
          >
            {{ syncCtrl.cargando() ? 'Sincronizando...' : 'Sincronizar Lote Ahora' }}
          </button>
        </div>
      </div>

      @if (syncCtrl.error()) {
        <div class="p-3 bg-red-50 text-red-700 text-xs rounded-xl mb-4">{{ syncCtrl.error() }}</div>
      }

      <div class="bg-white border rounded-2xl shadow-sm overflow-hidden">
        <table class="w-full text-left text-sm">
          <thead class="bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase">
            <tr>
              <th class="px-6 py-3">UUID</th>
              <th class="px-6 py-3">Tipo</th>
              <th class="px-6 py-3">Fecha Local</th>
              <th class="px-6 py-3">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            @for (op of colaCtrl.operaciones(); track op.id) {
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 font-mono text-xs font-bold text-gray-900">{{ op.id }}</td>
                <td class="px-6 py-4 font-semibold text-xs">{{ op.tipo }}</td>
                <td class="px-6 py-4 text-xs text-gray-500">{{ op.creada_en | date:'short' }}</td>
                <td class="px-6 py-4">
                  <span
                    [class]="op.estado === 'confirmada' ? 'bg-green-100 text-green-800' : op.estado === 'en_conflicto' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'"
                    class="px-2.5 py-0.5 rounded-full text-xs font-bold"
                  >
                    {{ op.estado }}
                  </span>
                </td>
              </tr>
            } @empty {
              <tr>
                <td colspan="4" class="px-6 py-8 text-center text-gray-400 text-xs">
                  Todas las operaciones están sincronizadas con el servidor central.
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `
})
export class ColaOperacionesComponent implements OnInit {
  colaCtrl = inject(CU30ColaOperacionesOfflineController);
  syncCtrl = inject(CU31SincronizarOperacionesController);

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.colaCtrl.cargarCola();
  }

  sincronizar() {
    this.syncCtrl.sincronizarLote().subscribe({
      next: () => this.cargar(),
      error: () => this.cargar()
    });
  }
}

