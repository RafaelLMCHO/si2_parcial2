import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import {
  CU27BloquearStockSoftLockController,
  SoftLockItem,
} from '../../../controller/cu27_bloquear_stock_soft_lock_controller';

@Component({
  selector: 'app-bloqueos-activos',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-5xl font-sans">
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid #e5e7eb;">
        <a routerLink="/offline/reserva" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-26: Reserva Offline</a>
        <a routerLink="/offline/bloqueos" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; background: #fdf2f8; color: #be185d; text-decoration: none;">CU-27: Bloqueos Activos (Soft-Lock)</a>
        <a routerLink="/offline/cola" style="padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; color: #4b5563; text-decoration: none;">CU-30/31: Cola y Sync</a>
      </div>

      <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-27: Bloqueos Activos de Stock (Soft-Lock TTL)</h1>
          <p class="text-sm text-gray-500">
            Control temporal de existencias apartadas durante reservas offline o en tienda (TTL predeterminado 45 min)
          </p>
        </div>
        <button
          (click)="recargar()"
          [disabled]="ctrl.cargando()"
          class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-xs font-bold rounded-xl"
        >
          {{ ctrl.cargando() ? 'Actualizando...' : 'Actualizar Lista' }}
        </button>
      </div>

      @if (mensaje()) {
        <div class="mb-4 p-3 rounded-xl bg-green-50 border border-green-200 text-green-800 text-xs font-semibold">
          {{ mensaje() }}
        </div>
      }

      @if (ctrl.error()) {
        <div class="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs font-semibold">
          {{ ctrl.error() }}
        </div>
      }

      <!-- Formulario para aplicar nuevo Soft-Lock -->
      <div class="bg-white border rounded-2xl p-5 shadow-sm mb-6">
        <h2 class="text-sm font-bold text-gray-800 mb-3">Crear Nuevo Soft-Lock</h2>
        <div class="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          <div>
            <label class="block text-xs font-bold text-gray-600 uppercase mb-1">Sucursal ID</label>
            <input [(ngModel)]="sucursalId" class="w-full text-xs px-3 py-2 border rounded-lg font-mono" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-600 uppercase mb-1">Variante ID</label>
            <input [(ngModel)]="varianteId" class="w-full text-xs px-3 py-2 border rounded-lg font-mono" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-600 uppercase mb-1">Cantidad</label>
            <input type="number" min="1" [(ngModel)]="cantidad" class="w-full text-xs px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-600 uppercase mb-1">TTL (minutos)</label>
            <input type="number" min="1" max="120" [(ngModel)]="ttlMinutos" class="w-full text-xs px-3 py-2 border rounded-lg" />
          </div>
          <button
            (click)="crearBloqueo()"
            [disabled]="ctrl.cargando()"
            class="py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition"
          >
            Bloquear Stock
          </button>
        </div>
      </div>

      <!-- Tabla de bloqueos activos -->
      <div class="bg-white border rounded-2xl shadow-sm overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase">
            <tr>
              <th class="px-5 py-3">Prenda / Variante</th>
              <th class="px-5 py-3">Sucursal / Dispositivo</th>
              <th class="px-5 py-3">Cantidad</th>
              <th class="px-5 py-3">TTL Restante</th>
              <th class="px-5 py-3">Origen</th>
              <th class="px-5 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            @for (b of ctrl.bloqueos(); track b.id) {
              <tr class="hover:bg-gray-50">
                <td class="px-5 py-4">
                  <div class="font-semibold text-gray-900 text-xs">
                    {{ b.prenda_nombre || 'Variante reservada' }}
                    @if (b.talla || b.color) {
                      <span class="text-gray-500 font-normal">({{ b.talla || '-' }} / {{ b.color || '-' }})</span>
                    }
                  </div>
                  <div class="font-mono text-[11px] text-gray-500">
                    {{ b.sku ? 'SKU: ' + b.sku + ' · ' : '' }}{{ b.variante_id }}
                  </div>
                </td>
                <td class="px-5 py-4 text-xs text-gray-600">
                  <div>{{ b.sucursal_nombre || b.sucursal_id || 'Sucursal local' }}</div>
                  <div class="text-[11px] text-gray-400">Dispositivo: {{ b.dispositivo_id || 'N/A' }}</div>
                </td>
                <td class="px-5 py-4 font-bold text-indigo-700">{{ b.cantidad }} u.</td>
                <td class="px-5 py-4">
                  <span
                    class="px-2.5 py-1 rounded-full text-xs font-mono font-bold"
                    [class]="b.ttl_restante_segundos <= 300 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-800'"
                  >
                    {{ formatearTtl(b.ttl_restante_segundos) }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <span
                    class="px-2 py-0.5 rounded-full text-[11px] font-semibold"
                    [class]="b.origen === 'servidor' ? 'bg-indigo-50 text-indigo-700' : 'bg-gray-100 text-gray-700'"
                  >
                    {{ b.origen === 'servidor' ? 'Servidor' : 'Local Offline' }}
                  </span>
                </td>
                <td class="px-5 py-4 text-right space-x-2 whitespace-nowrap">
                  <a
                    [routerLink]="['/offline/reserva']"
                    [queryParams]="{ sucursal_id: b.sucursal_id, variante_id: b.variante_id, cantidad: b.cantidad }"
                    class="inline-block px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold"
                  >
                    Reservar
                  </a>
                  <button
                    (click)="liberar(b)"
                    class="px-2.5 py-1 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg text-xs font-semibold"
                  >
                    Liberar
                  </button>
                </td>
              </tr>
            } @empty {
              <tr>
                <td colspan="6" class="px-6 py-8 text-center text-gray-400 text-xs">
                  No hay bloqueos soft-lock activos en este momento.
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
})
export class BloqueosActivosComponent implements OnInit, OnDestroy {
  readonly ctrl = inject(CU27BloquearStockSoftLockController);

  sucursalId = '11111111-1111-1111-1111-111111111101';
  varianteId = '22222222-2222-2222-2222-222222222201';
  cantidad = 1;
  ttlMinutos = 45;
  mensaje = signal<string | null>(null);

  private timerId: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.recargar();
    this.timerId = setInterval(() => {
      this.ctrl.refrescarTtlVisual();
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.timerId) {
      clearInterval(this.timerId);
    }
  }

  recargar(): void {
    this.ctrl.listarBloqueosActivos().subscribe();
  }

  crearBloqueo(): void {
    this.mensaje.set(null);
    this.ctrl
      .crearBloqueoServidor({
        sucursal_id: this.sucursalId,
        variante_id: this.varianteId,
        cantidad: Number(this.cantidad) || 1,
        ttl_minutos: Number(this.ttlMinutos) || 45,
      })
      .subscribe({
        next: () => {
          this.mensaje.set('Bloqueo temporal creado correctamente.');
        },
        error: () => {
          // Error ya expuesto en ctrl.error()
        },
      });
  }

  liberar(lock: SoftLockItem): void {
    this.mensaje.set(null);
    this.ctrl.liberarBloqueo(lock).subscribe({
      next: () => {
        this.mensaje.set(`Bloqueo ${lock.id} liberado.`);
      },
    });
  }

  formatearTtl(segundos: number): string {
    const s = Math.max(0, Math.floor(segundos));
    const min = Math.floor(s / 60);
    const rem = s % 60;
    return `${String(min).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
  }
}

