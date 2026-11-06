import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CU29ValidarQrCambioOfflineController } from '../../../controller/cu29_validar_qr_cambio_offline_controller';

@Component({
  selector: 'app-cambio-qr',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-3xl font-sans">
      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-29: Validar Comprobante QR y Cambio Offline</h1>
        <p class="text-sm text-gray-500">Validación de autenticidad criptográfica y control de plazo de 30 días (BR-10)</p>
      </div>

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Contenido QR del Ticket</label>
          <textarea [(ngModel)]="qrInput" rows="3" class="w-full text-xs font-mono px-3 py-2 border rounded-lg"></textarea>
        </div>

        <button (click)="validar()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs">
          Validar Firma y Plazo
        </button>

        @if (ctrl.error()) {
          <div class="p-3 bg-red-50 text-red-700 text-xs rounded-xl">{{ ctrl.error() }}</div>
        }

        @if (ctrl.ticketValidado(); as t) {
          <div class="p-4 bg-green-50 border border-green-200 rounded-xl space-y-2">
            <div class="font-bold text-green-900 text-xs">Comprobante Válido (Dentro del plazo de 30 días)</div>
            <div class="text-xs text-gray-700">Ticket UUID: {{ t.uuid }} • Total: BOB {{ t.total }}</div>
          </div>

          <div class="pt-4 border-t space-y-3">
            <label class="block text-xs font-bold text-gray-700 uppercase">Motivo del Cambio</label>
            <input [(ngModel)]="motivo" class="w-full text-sm px-3 py-2 border rounded-lg" />

            <button
              (click)="procesar()"
              class="w-full py-2.5 bg-indigo-600 text-white font-bold rounded-xl text-xs hover:bg-indigo-700"
            >
              Confirmar Cambio y Emitir Nota Preliminar
            </button>
          </div>
        }

        @if (ctrl.notaCambio(); as nc) {
          <div class="p-3 bg-blue-50 text-blue-800 text-xs rounded-xl font-bold">
            Nota de Cambio registrada en cola: {{ nc.uuid }}
          </div>
        }
      </div>
    </div>
  `
})
export class CambioQrComponent {
  ctrl = inject(CU29ValidarQrCambioOfflineController);
  qrInput = JSON.stringify({
    uuid: 'ticket-demo-4567',
    fecha_hora_local: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString(),
    total: 120.0
  });
  motivo = 'Cambio de color por preferencia del cliente';

  validar() {
    this.ctrl.validarQr(this.qrInput);
  }

  procesar() {
    this.ctrl.procesarCambio({
      sucursal_id: '11111111-1111-1111-1111-111111111101',
      variante_devuelta_id: '22222222-2222-2222-2222-222222222201',
      variante_nueva_id: '22222222-2222-2222-2222-222222222202',
      motivo: this.motivo
    });
  }
}

