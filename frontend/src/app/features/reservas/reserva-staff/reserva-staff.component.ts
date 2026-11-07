import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ReservaService } from '../../../core/reserva.service';

@Component({
  selector: 'app-reserva-staff',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-5xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/reservas/nueva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-20: Mis Reservas / Consulta</a>
        <a routerLink="/reservas/staff" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-21: Preparación Staff Tienda</a>
      </div>

      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-21: Validación y Preparación de Reservas (Staff)</h1>
          <p class="text-sm text-gray-500">Módulo de tienda para apartar prendas en probador y registrar entrega</p>
        </div>
        <button (click)="cargar()" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-sm font-semibold rounded-lg">
          Actualizar
        </button>
      </div>

      <div class="bg-white border rounded-2xl shadow-sm overflow-hidden">
        <table class="w-full text-left text-sm">
          <thead class="bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase">
            <tr>
              <th class="px-6 py-3">Código</th>
              <th class="px-6 py-3">Cliente</th>
              <th class="px-6 py-3">Fecha Visita</th>
              <th class="px-6 py-3">Probador</th>
              <th class="px-6 py-3">Estado</th>
              <th class="px-6 py-3 text-right">Acciones Staff</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            @for (r of reservas(); track r.id) {
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 font-mono font-bold text-indigo-700">{{ r.codigo || r.id.slice(0, 8) }}</td>
                <td class="px-6 py-4">{{ r.cliente_email || 'Cliente' }}</td>
                <td class="px-6 py-4 text-gray-500">{{ r.fecha_visita | date:'short' }}</td>
                <td class="px-6 py-4">
                  <span [class]="r.probador ? 'text-purple-700 font-semibold' : 'text-gray-400'">
                    {{ r.probador ? 'Sí' : 'No' }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800">
                    {{ r.estado }}
                  </span>
                </td>
                <td class="px-6 py-4 text-right space-x-2">
                  <button
                    (click)="preparar(r.id)"
                    class="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded text-xs font-semibold"
                  >
                    Preparar
                  </button>
                  <button
                    (click)="completar(r.id)"
                    class="px-2.5 py-1 bg-green-50 hover:bg-green-100 text-green-700 rounded text-xs font-semibold"
                  >
                    Entregar
                  </button>
                </td>
              </tr>
            } @empty {
              <tr><td colspan="6" class="px-6 py-8 text-center text-gray-400">No hay reservas pendientes en la sucursal.</td></tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `
})
export class ReservaStaffComponent implements OnInit {
  private reservaService = inject(ReservaService);
  cargando = signal(false);
  reservas = signal<any[]>([]);

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.reservaService.listarReservas().subscribe({
      next: (res: any) => {
        this.reservas.set(res.items || []);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }

  preparar(id: string) {
    this.reservaService.prepararReserva(id).subscribe({ next: () => this.cargar() });
  }

  completar(id: string) {
    this.reservaService.completarReserva(id).subscribe({ next: () => this.cargar() });
  }
}

