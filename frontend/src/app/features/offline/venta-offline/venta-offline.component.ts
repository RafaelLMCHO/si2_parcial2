import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CU27BloquearStockSoftLockController } from '../../../controller/cu27_bloquear_stock_soft_lock_controller';
import { CU28VentaContadoOfflineController } from '../../../controller/cu28_venta_contado_offline_controller';

@Component({
  selector: 'app-venta-offline',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-3xl font-sans">
      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-27 y CU-28: Venta de Contado Offline (Soft-Lock)</h1>
        <p class="text-sm text-gray-500">Cobro presencial en efectivo (Sección 7.2) y comprobante preliminar (BR-11)</p>
      </div>

      <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl mb-6 text-xs text-amber-800">
        ⚠️ Restricción Normativa: En contingencia offline solo se permiten ventas de contado en efectivo. Las prendas se bloquean con Soft-Lock (TTL 45 min).
      </div>

      <div class="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Cliente</label>
            <input [(ngModel)]="clienteNombre" class="w-full text-sm px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-700 uppercase mb-1">NIT / CI</label>
            <input [(ngModel)]="clienteDoc" class="w-full text-sm px-3 py-2 border rounded-lg" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Forma de Pago</label>
          <select [(ngModel)]="formaPago" class="w-full text-sm px-3 py-2 border rounded-lg bg-gray-50">
            <option value="efectivo">Efectivo / Contado (Permitido)</option>
            <option value="tarjeta" disabled>Tarjeta / Electrónico (Bloqueado offline)</option>
          </select>
        </div>

        <div class="border rounded-xl p-4 bg-gray-50">
          <div class="flex justify-between items-center text-sm">
            <span>Camisa Oxford M (SKU: OX-M) x 1</span>
            <span class="font-bold">BOB 120.00</span>
          </div>
        </div>

        <button
          (click)="confirmarVenta()"
          class="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl text-sm transition"
        >
          Confirmar Venta Offline e Imprimir Ticket (BR-11)
        </button>

        @if (ventaCtrl.ticketPreliminar(); as t) {
          <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-xl space-y-2">
            <div class="font-bold text-xs uppercase text-yellow-800 tracking-wider">
              {{ t.leyenda_ticket }}
            </div>
            <div class="text-xs text-gray-700">
              UUID: <strong class="font-mono">{{ t.uuid }}</strong><br>
              Cliente: {{ t.cliente_nombre }} • Total: BOB {{ t.total }}
            </div>
            <div class="text-[11px] text-gray-500">
              Soft-lock aplicado con TTL de 45 minutos en el almacenamiento local (CU-27).
            </div>
          </div>
        }
      </div>
    </div>
  `
})
export class VentaOfflineComponent {
  lockCtrl = inject(CU27BloquearStockSoftLockController);
  ventaCtrl = inject(CU28VentaContadoOfflineController);

  clienteNombre = 'Consumidor Final';
  clienteDoc = '0';
  formaPago = 'efectivo';

  confirmarVenta() {
    // 1. Soft-Lock TTL 45 min
    this.lockCtrl.bloquearStock('22222222-2222-2222-2222-222222222201', 1, 45);

    // 2. Venta contado offline
    this.ventaCtrl.registrarVenta({
      sucursal_id: '11111111-1111-1111-1111-111111111101',
      usuario_id: 'cajero-01',
      cliente_nombre: this.clienteNombre,
      cliente_documento: this.clienteDoc,
      lineas: [{
        variante_id: '22222222-2222-2222-2222-222222222201',
        sku: 'OX-M',
        cantidad: 1,
        precio_unitario: 120.0
      }],
      total: 120.0,
      metodo_pago: this.formaPago
    });
  }
}

