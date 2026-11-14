import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { CU32ResolverConflictosController } from '../../../controller/cu32_resolver_conflictos_controller';
import { VentasOfflineStore } from '../../../core/ventas-offline-store.service';
import { OfflineQueueService } from '../../../core/offline-queue.service';

@Component({
  selector: 'app-conflictos-sync',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-5xl font-sans">
      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-32: Bandeja de Conflictos de Sincronización</h1>
          <p class="text-sm text-gray-500">Resolución con políticas FIFO, regularización de stock o anulación</p>
        </div>
        <button (click)="cargar()" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs font-semibold rounded-lg">
          Actualizar
        </button>
      </div>

      @if (ctrl.error()) {
        <div class="p-3 bg-red-50 text-red-700 text-xs rounded-xl mb-4">
          ⚠️ {{ ctrl.error() }}
        </div>
      }

      <div class="space-y-4">
        @for (c of ctrl.conflictos(); track c.id) {
          <div class="bg-white border rounded-2xl p-5 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="font-mono font-bold text-xs text-red-700">{{ c.id }}</span>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-100 text-red-800">EN CONFLICTO</span>
                <span class="text-xs text-gray-400">• {{ c.tipo }}</span>
              </div>
              <p class="text-xs text-red-600 font-medium">Causa: {{ c.ultimo_error || 'Stock central insuficiente' }}</p>
            </div>

            <div class="flex gap-2">
              <button
                [disabled]="resolviendoId() === c.id"
                (click)="resolver(c, 'rechazar')"
                class="px-3 py-1.5 border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-xs rounded-lg disabled:opacity-50"
              >
                Anular Venta
              </button>
              <button
                [disabled]="resolviendoId() === c.id"
                (click)="resolver(c, 'ajustar')"
                class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg disabled:opacity-50"
              >
                {{ resolviendoId() === c.id ? 'Ajustando...' : 'Ajustar Stock (FIFO)' }}
              </button>
            </div>
          </div>
        } @empty {
          <div class="bg-gray-50 border rounded-2xl p-12 text-center text-gray-400 text-sm">
            No existen conflictos de sincronización pendientes de resolver.
          </div>
        }
      </div>
    </div>
  `
})
export class ConflictosSyncComponent implements OnInit {
  ctrl = inject(CU32ResolverConflictosController);
  ventasStore = inject(VentasOfflineStore);
  offlineQueue = inject(OfflineQueueService);

  resolviendoId = signal<string | null>(null);

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.ctrl.cargarConflictos().subscribe();
  }

  resolver(c: any, decision: 'ajustar' | 'rechazar') {
    this.resolviendoId.set(c.id);
    this.ctrl.resolverConflicto({
      operacion_id: c.id,
      decision,
      motivo: 'Resolución manual desde panel web'
    }).subscribe({
      next: () => {
        this.resolviendoId.set(null);
        const localId = c.payload?.uuid || c.id;
        if (decision === 'ajustar') {
          this.ventasStore.applySyncResult([localId], []);
        } else {
          this.ventasStore.remove(localId);
        }
        this.offlineQueue.refreshStatus();
      },
      error: () => {
        this.resolviendoId.set(null);
      }
    });
  }
}

