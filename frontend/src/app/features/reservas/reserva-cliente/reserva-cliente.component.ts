import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
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
        <button (click)="cargar()" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-sm font-semibold rounded-lg">
          Actualizar
        </button>
      </div>

      @if (cargando()) {
        <div class="flex justify-center p-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
      } @else {
        <div class="space-y-4">
          @for (r of reservas(); track r.id) {
            <div class="bg-white border rounded-2xl p-5 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-mono font-bold text-sm text-indigo-700">{{ r.codigo || r.id.slice(0, 8) }}</span>
                  <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700">
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
              </div>

              @if (r.estado === 'activa' || r.estado === 'pendiente_preparacion' || r.estado === 'preparada') {
                <button
                  (click)="cancelar(r.id)"
                  class="px-4 py-1.5 border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold rounded-lg"
                >
                  Cancelar Reserva
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
  private reservaService = inject(ReservaService);
  cargando = signal(false);
  reservas = signal<any[]>([]);

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
      error: () => this.cargando.set(false)
    });
  }

  cancelar(id: string) {
    if (!confirm('¿Deseas cancelar esta reserva?')) return;
    this.reservaService.cancelarReserva(id, 'Cancelado por el cliente').subscribe({
      next: () => this.cargar()
    });
  }
}

