import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CU31SincronizarOperacionesController } from '../../../controller/cu31_sincronizar_operaciones_controller';
import { NetworkService } from '../../../core/network.service';
import { ReservaService } from '../../../core/reserva.service';

@Component({
  selector: 'app-reserva-cliente',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-4xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/reservas/nueva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-20: Mis Reservas / Consulta</a>
        <a routerLink="/reservas/staff" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-21: Preparación Staff Tienda</a>
      </div>

      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-20: Mis Reservas</h1>
          <p class="text-sm text-gray-500">Historial y estado de tus prendas y probadores reservados</p>
        </div>
        <div class="flex gap-2">
          @if (pendientesCount() > 0 && network.online()) {
            <button
              (click)="sincronizarPendientes()"
              [disabled]="syncCtrl.cargando()"
              class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg disabled:opacity-50"
            >
              {{ syncCtrl.cargando() ? 'Sincronizando...' : 'Sincronizar Pendientes (' + pendientesCount() + ')' }}
            </button>
          }
          <button (click)="cargar()" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-sm font-semibold rounded-lg">
            Actualizar
          </button>
        </div>
      </div>

      @if (syncMensaje()) {
        <div class="mb-4 p-3 bg-indigo-50 border border-indigo-200 text-indigo-800 rounded-xl text-xs font-semibold">
          {{ syncMensaje() }}
        </div>
      }

      @if (pendientesCount() > 0) {
        <div class="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl text-xs font-semibold">
          Tienes {{ pendientesCount() }} reserva(s) local(es) pendiente(s) o en revisión de sincronización (CU-26/CU-31).
        </div>
      }

      @if (cargando()) {
        <div class="flex justify-center p-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
      } @else {
        <div class="space-y-4">
          @for (r of reservas(); track r.id) {
            <div class="bg-white border rounded-2xl p-5 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <div class="flex items-center flex-wrap gap-2 mb-1">
                  <span class="font-mono font-bold text-sm text-indigo-700">{{ r.codigo || r.id.slice(0, 8) }}</span>
                  <span
                    [class]="r.estado === 'conflicto_sync' ? 'bg-red-100 text-red-700' : r.estado === 'pendiente_sync' ? 'bg-amber-100 text-amber-800' : 'bg-indigo-50 text-indigo-700'"
                    class="px-2 py-0.5 rounded-full text-xs font-semibold"
                  >
                    {{ r.estado }}
                  </span>
                  @if (r.probador) {
                    <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700">
                      Probador Apartado
                    </span>
                  }
                </div>
                <div class="text-xs text-gray-500">
                  Fecha de Visita: <strong class="text-gray-800">{{ r.fecha_visita | date:'short' }}</strong> • Sucursal: {{ r.sucursal_nombre || r.sucursal_id }}
                </div>
                @if (r.items && r.items.length > 0) {
                  <ul class="mt-2 text-xs text-gray-600 list-disc pl-4">
                    @for (it of r.items; track it.variante_id) {
                      <li>{{ it.prenda_nombre }} ({{ it.talla }} / {{ it.color }}) — Cant: {{ it.cantidad }}</li>
                    }
                  </ul>
                }
                @if (r.estado === 'conflicto_sync' && r.message) {
                  <div class="mt-1 text-xs text-red-600 font-medium">Conflicto: {{ r.message }}</div>
                }
              </div>

              @if (r.estado === 'activa' || r.estado === 'pendiente_preparacion' || r.estado === 'preparada' || r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync') {
                <button
                  (click)="cancelar(r.id)"
                  class="px-4 py-1.5 border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold rounded-lg"
                >
                  {{ r.offline ? 'Eliminar Pendiente' : 'Cancelar Reserva' }}
                </button>
              }
            </div>
          } @empty {
            <div class="bg-gray-50 border rounded-2xl p-8 text-center text-gray-500 text-sm">
              No tienes reservas activas en este momento.
            </div>
          }
        </div>
      }
    </div>
  `
})
export class ReservaClienteComponent implements OnInit {
  private readonly reservaService = inject(ReservaService);
  readonly syncCtrl = inject(CU31SincronizarOperacionesController);
  readonly network = inject(NetworkService);

  cargando = signal(false);
  reservas = signal<any[]>([]);
  syncMensaje = signal<string | null>(null);

  pendientesCount = computed(() =>
    this.reservas().filter((r) => r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync').length,
  );

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.reservaService.obtenerMisReservas().subscribe({
      next: (res: any) => {
        this.reservas.set(res.items || []);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  sincronizarPendientes() {
    this.syncMensaje.set(null);
    this.syncCtrl.sincronizarLote().subscribe({
      next: (res) => {
        const ok = (res?.confirmados || []).length;
        const conf = (res?.conflictos || []).length;
        this.syncMensaje.set(`Sincronización finalizada: ${ok} confirmada(s), ${conf} en conflicto.`);
        this.cargar();
      },
      error: (err) => {
        this.syncMensaje.set(err?.message || 'No se pudo sincronizar en este momento.');
        this.cargar();
      },
    });
  }

  cancelar(id: string) {
    if (!confirm('¿Deseas cancelar esta reserva?')) return;
    this.reservaService.cancelarReserva(id, 'Cancelado por el cliente').subscribe({
      next: () => this.cargar(),
    });
  }
}

