import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ReservaService } from '../../../core/reserva.service';

@Component({
  selector: 'app-reserva-creacion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-2xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/reservas/nueva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-20: Mis Reservas / Consulta</a>
        <a routerLink="/reservas/staff" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-21: Preparación Staff Tienda</a>
      </div>

      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-19: Reserva de Prendas y Probador</h1>
        <p class="text-sm text-gray-500">Agenda tu visita para probarte prendas en tienda sin compromiso de compra</p>
      </div>

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Sucursal de Visita</label>
          <input
            type="text"
            [(ngModel)]="sucursalId"
            placeholder="UUID de la Sucursal..."
            class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Fecha y Hora de Visita</label>
          <input
            type="datetime-local"
            [(ngModel)]="fechaVisita"
            class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div class="flex items-center gap-2">
          <input type="checkbox" id="probador" [(ngModel)]="requiereProbador" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="probador" class="text-sm text-gray-700 font-medium">Apartar cabina de probador</label>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Variante a Probar (UUID)</label>
          <input
            type="text"
            [(ngModel)]="varianteId"
            placeholder="UUID de la variante..."
            class="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <button
          (click)="crear()"
          [disabled]="cargando()"
          class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition disabled:opacity-50"
        >
          {{ cargando() ? 'Creando reserva...' : 'Confirmar Reserva (CU-19)' }}
        </button>

        @if (mensaje()) {
          <div class="p-3 bg-green-50 text-green-800 border border-green-200 rounded-xl text-xs font-semibold">
            {{ mensaje() }}
          </div>
        }
      </div>
    </div>
  `
})
export class ReservaCreacionComponent {
  private reservaService = inject(ReservaService);

  sucursalId = '11111111-1111-1111-1111-111111111101';
  fechaVisita = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 16);
  requiereProbador = true;
  varianteId = '22222222-2222-2222-2222-222222222201';

  cargando = signal(false);
  mensaje = signal<string | null>(null);

  crear() {
    this.cargando.set(true);
    this.mensaje.set(null);

    this.reservaService.crearReserva({
      sucursal_id: this.sucursalId,
      fecha_visita: new Date(this.fechaVisita).toISOString(),
      probador: this.requiereProbador,
      items: [{ variante_id: this.varianteId, cantidad: 1 }]
    }).subscribe({
      next: (res: any) => {
        this.mensaje.set(`¡Reserva creada exitosamente! Código: ${res.codigo || res.id}`);
        this.cargando.set(false);
      },
      error: (err: any) => {
        this.mensaje.set(`Error: ${err.message || 'No se pudo crear la reserva'}`);
        this.cargando.set(false);
      }
    });
  }
}

