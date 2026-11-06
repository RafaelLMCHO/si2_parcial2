import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CU26RegistrarReservaOfflineController } from '../../../controller/cu26_registrar_reserva_offline_controller';

@Component({
  selector: 'app-reserva-offline',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-2xl font-sans">
      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-26: Registrar Reserva Offline (UUID Local)</h1>
        <p class="text-sm text-gray-500">Genera una reserva persistida en la cola local para su posterior confirmación en servidor</p>
      </div>

      <div class="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 text-xs text-amber-800">
        ⚠️ Modo Desconectado: La reserva se almacenará en la cola Outbox con identificador UUID v4 único.
      </div>

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Sucursal ID</label>
          <input [(ngModel)]="sucursalId" class="w-full text-sm px-3 py-2 border rounded-lg" />
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Variante ID</label>
          <input [(ngModel)]="varianteId" class="w-full text-sm px-3 py-2 border rounded-lg" />
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" id="probador" [(ngModel)]="probador" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="probador" class="text-sm font-medium text-gray-700">Apartar cabina de probador</label>
        </div>

        <button
          (click)="guardar()"
          class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition"
        >
          Guardar Reserva en Cola Outbox
        </button>

        @if (ctrl.reservaUuid(); as uuid) {
          <div class="p-3 bg-green-50 text-green-800 border border-green-200 rounded-xl text-xs font-semibold">
            Reserva registrada localmente con UUID: {{ uuid }}
          </div>
        }
      </div>
    </div>
  `
})
export class ReservaOfflineComponent {
  ctrl = inject(CU26RegistrarReservaOfflineController);
  sucursalId = '11111111-1111-1111-1111-111111111101';
  varianteId = '22222222-2222-2222-2222-222222222201';
  probador = true;

  guardar() {
    this.ctrl.registrarReserva({
      sucursal_id: this.sucursalId,
      fecha_visita: new Date(Date.now() + 24 * 3600 * 1000).toISOString(),
      probador: this.probador,
      items: [{ variante_id: this.varianteId, cantidad: 1 }]
    });
  }
}

