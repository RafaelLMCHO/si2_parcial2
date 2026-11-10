import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CU26RegistrarReservaOfflineController } from '../../../controller/cu26_registrar_reserva_offline_controller';
import { CU27BloquearStockSoftLockController } from '../../../controller/cu27_bloquear_stock_soft_lock_controller';

@Component({
  selector: 'app-reserva-offline',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-2xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/offline/reserva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-26: Reserva Offline</a>
        <a routerLink="/offline/bloqueos" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">
          CU-27: Bloqueos Activos ({{ softLockCtrl.bloqueos().length }})
        </a>
        <a routerLink="/offline/cola" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-30/31: Cola y Sync</a>
      </div>

      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-26: Registrar Reserva Offline (UUID Local)</h1>
        <p class="text-sm text-gray-500">Genera una reserva persistida en la cola local y opcionalmente aplica soft-lock temporal (CU-27)</p>
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
        <div>
          <label class="block text-xs font-bold text-gray-700 uppercase mb-1">Cantidad</label>
          <input type="number" min="1" [(ngModel)]="cantidad" class="w-full text-sm px-3 py-2 border rounded-lg" />
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" id="probador" [(ngModel)]="probador" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="probador" class="text-sm font-medium text-gray-700">Apartar cabina de probador</label>
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" id="aplicarSoftLock" [(ngModel)]="aplicarSoftLock" class="h-4 w-4 text-indigo-600 rounded" />
          <label for="aplicarSoftLock" class="text-sm font-medium text-gray-700">Aplicar Soft-Lock temporal de 45 min (CU-27)</label>
        </div>

        <button
          (click)="guardar()"
          class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition"
        >
          Guardar Reserva en Cola Outbox
        </button>

        @if (ctrl.reservaUuid(); as uuid) {
          <div class="p-3 bg-green-50 text-green-800 border border-green-200 rounded-xl text-xs font-semibold flex justify-between items-center gap-2">
            <span>Reserva registrada localmente con UUID: {{ uuid }}</span>
            <a routerLink="/offline/bloqueos" class="underline font-bold">Ver bloqueos ({{ softLockCtrl.bloqueos().length }})</a>
          </div>
        }
      </div>
    </div>
  `
})
export class ReservaOfflineComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly ctrl = inject(CU26RegistrarReservaOfflineController);
  readonly softLockCtrl = inject(CU27BloquearStockSoftLockController);

  sucursalId = '11111111-1111-1111-1111-111111111101';
  varianteId = '22222222-2222-2222-2222-222222222201';
  cantidad = 1;
  probador = true;
  aplicarSoftLock = true;

  ngOnInit(): void {
    const qp = this.route.snapshot.queryParamMap;
    if (qp.get('sucursal_id')) this.sucursalId = qp.get('sucursal_id')!;
    if (qp.get('variante_id')) this.varianteId = qp.get('variante_id')!;
    if (qp.get('cantidad')) this.cantidad = Math.max(1, Number(qp.get('cantidad')) || 1);
    this.softLockCtrl.listarBloqueosActivos().subscribe();
  }

  guardar() {
    const qty = Math.max(1, Number(this.cantidad) || 1);
    if (this.aplicarSoftLock) {
      this.softLockCtrl.bloquearStock(this.varianteId, qty, 45, this.sucursalId);
    }
    this.ctrl.registrarReserva({
      sucursal_id: this.sucursalId,
      fecha_visita: new Date(Date.now() + 24 * 3600 * 1000).toISOString(),
      probador: this.probador,
      items: [{ variante_id: this.varianteId, cantidad: qty }]
    });
  }
}
