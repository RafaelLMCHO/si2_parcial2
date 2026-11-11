import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CU31SincronizarOperacionesController } from '../../../controller/cu31_sincronizar_operaciones_controller';
import { AuthService } from '../../../core/auth.service';
import { NetworkService } from '../../../core/network.service';
import { ReservaService } from '../../../core/reserva.service';
import { extraerMensajeErrorReserva } from '../reserva-creacion/reserva-creacion.component';

@Component({
  selector: 'app-reserva-cliente',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="rc-page">
      <div class="rc-tabs">
        <a routerLink="/reservas/nueva" class="rc-tab">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" class="rc-tab active">CU-20: Mis Reservas / Consulta</a>
        @if (esStaff()) {
          <a routerLink="/reservas/staff" class="rc-tab">CU-21: Preparación Staff Tienda</a>
        }
      </div>

      <header class="rc-header">
        <div>
          <span class="rc-badge-tag">Citas y Apartados</span>
          <h1 class="rc-title">CU-20: Mis Reservas</h1>
          <p class="rc-subtitle">Historial y estado de tus prendas y probadores reservados</p>
        </div>
        <div class="rc-header-actions">
          @if (pendientesCount() > 0 && network.online()) {
            <button
              type="button"
              (click)="sincronizarPendientes()"
              [disabled]="syncCtrl.cargando()"
              class="rc-btn rc-btn-indigo"
            >
              {{ syncCtrl.cargando() ? 'Sincronizando...' : 'Sincronizar Pendientes (' + pendientesCount() + ')' }}
            </button>
          }
          <button type="button" (click)="cargar()" class="rc-btn rc-btn-ghost">
            Actualizar
          </button>
          <a routerLink="/reservas/nueva" class="rc-btn rc-btn-primary">
            + Nueva Reserva
          </a>
        </div>
      </header>

      @if (errorMensaje()) {
        <div class="rc-banner error" role="alert">
          {{ errorMensaje() }}
        </div>
      }

      @if (syncMensaje()) {
        <div class="rc-banner info" role="status">
          {{ syncMensaje() }}
        </div>
      }

      @if (pendientesCount() > 0) {
        <div class="rc-banner warning">
          Tienes {{ pendientesCount() }} reserva(s) local(es) pendiente(s) o en revisión de sincronización (CU-26/CU-31).
        </div>
      }

      @if (cargando()) {
        <div class="rc-loading">
          <div class="rc-spinner"></div>
          <span>Cargando tus reservas...</span>
        </div>
      } @else {
        <div class="rc-list">
          @for (r of reservas(); track r.id) {
            <div class="rc-card">
              <div class="rc-card-info">
                <div class="rc-badges-row">
                  <span class="rc-code">{{ r.codigo || r.id.slice(0, 8) }}</span>
                  <span
                    class="rc-status"
                    [class.conflict]="r.estado === 'conflicto_sync'"
                    [class.pending-sync]="r.estado === 'pendiente_sync'"
                    [class.ready]="r.estado === 'preparada' || r.estado === 'completada'"
                    [class.cancelled]="r.estado === 'cancelada'"
                  >
                    {{ r.estado }}
                  </span>
                  @if (r.probador) {
                    <span class="rc-chip-probador">Probador Apartado</span>
                  }
                </div>
                <div class="rc-meta">
                  Fecha de Visita: <strong>{{ r.fecha_visita | date:'short' }}</strong> • Sucursal: <strong>{{ r.sucursal_nombre || r.sucursal_id }}</strong>
                </div>
                @if (r.items && r.items.length > 0) {
                  <ul class="rc-items">
                    @for (it of r.items; track it.variante_id) {
                      <li>{{ it.prenda_nombre }} ({{ it.talla }} / {{ it.color }}) — Cant: {{ it.cantidad }}</li>
                    }
                  </ul>
                }
                @if (r.estado === 'conflicto_sync' && r.message) {
                  <div class="rc-conflict-msg">Conflicto: {{ r.message }}</div>
                }
              </div>

              @if (r.estado === 'activa' || r.estado === 'pendiente_preparacion' || r.estado === 'preparada' || r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync') {
                <button
                  type="button"
                  (click)="cancelar(r.id)"
                  class="rc-btn-cancel"
                >
                  {{ r.offline ? 'Eliminar Pendiente' : 'Cancelar Reserva' }}
                </button>
              }
            </div>
          } @empty {
            <div class="rc-empty">
              <p>No tienes reservas activas en este momento.</p>
              <a routerLink="/reservas/nueva" class="rc-btn rc-btn-primary">Reservar Probador Ahora</a>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .rc-page {
      max-width: 920px;
      margin: 0 auto;
      padding: 24px 16px 40px;
      color: #0f172a;
    }
    .rc-tabs {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 1.5rem;
      background: #ffffff;
      padding: 0.65rem 0.85rem;
      border-radius: 14px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .rc-tab {
      padding: 0.45rem 0.9rem;
      border-radius: 9px;
      font-size: 0.86rem;
      font-weight: 600;
      color: #475569;
      text-decoration: none;
    }
    .rc-tab:hover {
      background: #f8fafc;
      color: #0f172a;
    }
    .rc-tab.active {
      background: #fdf2f8;
      color: #be185d;
      font-weight: 700;
    }
    .rc-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .rc-badge-tag {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #be185d;
      background: #fdf2f8;
      border: 1px solid #fbcfe8;
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      margin-bottom: 0.45rem;
    }
    .rc-title {
      font-size: 1.65rem;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 0.25rem;
    }
    .rc-subtitle {
      margin: 0;
      font-size: 0.9rem;
      color: #64748b;
    }
    .rc-header-actions {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      align-items: center;
    }
    .rc-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.5rem 0.95rem;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 700;
      border: 1px solid transparent;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
    }
    .rc-btn-ghost {
      background: #ffffff;
      border-color: #cbd5e1;
      color: #334155;
    }
    .rc-btn-ghost:hover {
      background: #f8fafc;
    }
    .rc-btn-indigo {
      background: #4f46e5;
      color: #ffffff;
    }
    .rc-btn-indigo:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }
    .rc-btn-primary {
      background: linear-gradient(135deg, #be185d 0%, #9d174d 100%);
      color: #ffffff;
    }
    .rc-banner {
      padding: 0.85rem 1rem;
      border-radius: 12px;
      font-size: 0.84rem;
      font-weight: 600;
      margin-bottom: 1rem;
      border: 1px solid transparent;
    }
    .rc-banner.info {
      background: #eef2ff;
      border-color: #c7d2fe;
      color: #3730a3;
    }
    .rc-banner.warning {
      background: #fffbeb;
      border-color: #fde68a;
      color: #92400e;
    }
    .rc-banner.error {
      background: #fef2f2;
      border-color: #fecaca;
      color: #991b1b;
    }
    .rc-loading {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
      padding: 3rem 1rem;
      background: #ffffff;
      border-radius: 16px;
      border: 1px solid #e2e8f0;
      color: #64748b;
      font-size: 0.9rem;
    }
    .rc-spinner {
      width: 28px;
      height: 28px;
      border: 3px solid #e2e8f0;
      border-top-color: #be185d;
      border-radius: 50%;
      animation: rc-spin 0.8s linear infinite;
    }
    @keyframes rc-spin {
      to { transform: rotate(360deg); }
    }
    .rc-list {
      display: flex;
      flex-direction: column;
      gap: 0.9rem;
    }
    .rc-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.25rem;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .rc-card-info {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      flex: 1;
      min-width: 240px;
    }
    .rc-badges-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .rc-code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-weight: 800;
      font-size: 0.92rem;
      color: #4338ca;
    }
    .rc-status {
      padding: 0.18rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      background: #eef2ff;
      color: #3730a3;
    }
    .rc-status.pending-sync {
      background: #fef3c7;
      color: #92400e;
    }
    .rc-status.conflict {
      background: #fee2e2;
      color: #991b1b;
    }
    .rc-status.ready {
      background: #dcfce7;
      color: #166534;
    }
    .rc-status.cancelled {
      background: #f1f5f9;
      color: #64748b;
    }
    .rc-chip-probador {
      padding: 0.18rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.74rem;
      font-weight: 700;
      background: #fdf2f8;
      color: #be185d;
    }
    .rc-meta {
      font-size: 0.84rem;
      color: #475569;
    }
    .rc-items {
      margin: 0.35rem 0 0;
      padding-left: 1.2rem;
      font-size: 0.82rem;
      color: #334155;
    }
    .rc-conflict-msg {
      margin-top: 0.25rem;
      font-size: 0.8rem;
      color: #b91c1c;
      font-weight: 600;
    }
    .rc-btn-cancel {
      padding: 0.48rem 0.95rem;
      border-radius: 10px;
      border: 1px solid #fecaca;
      background: #ffffff;
      color: #dc2626;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
    }
    .rc-btn-cancel:hover {
      background: #fef2f2;
    }
    .rc-empty {
      background: #ffffff;
      border: 1px dashed #cbd5e1;
      border-radius: 16px;
      padding: 2.5rem 1.25rem;
      text-align: center;
      color: #64748b;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.9rem;
    }
    .rc-empty p {
      margin: 0;
      font-size: 0.95rem;
    }
  `],
})
export class ReservaClienteComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly reservaService = inject(ReservaService);
  readonly syncCtrl = inject(CU31SincronizarOperacionesController);
  readonly network = inject(NetworkService);

  esStaff = computed(() =>
    ['superadmin', 'administrador', 'encargado', 'cajero'].includes(this.auth.user()?.rol || ''),
  );

  cargando = signal(false);
  reservas = signal<any[]>([]);
  syncMensaje = signal<string | null>(null);
  errorMensaje = signal<string | null>(null);

  pendientesCount = computed(() =>
    this.reservas().filter((r) => r.estado === 'pendiente_sync' || r.estado === 'conflicto_sync').length,
  );

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.errorMensaje.set(null);
    this.reservaService.obtenerMisReservas().subscribe({
      next: (res: any) => {
        this.reservas.set(res.items || []);
        this.cargando.set(false);
      },
      error: (err) => {
        this.errorMensaje.set(extraerMensajeErrorReserva(err));
        this.cargando.set(false);
      },
    });
  }

  sincronizarPendientes() {
    this.syncMensaje.set(null);
    this.errorMensaje.set(null);
    this.syncCtrl.sincronizarLote().subscribe({
      next: (res) => {
        const ok = (res?.confirmados || []).length;
        const conf = (res?.conflictos || []).length;
        this.syncMensaje.set(`Sincronización finalizada: ${ok} confirmada(s), ${conf} en conflicto.`);
        this.cargar();
      },
      error: (err) => {
        this.errorMensaje.set(extraerMensajeErrorReserva(err));
        this.cargar();
      },
    });
  }

  cancelar(id: string) {
    if (!confirm('¿Deseas cancelar esta reserva?')) return;
    this.errorMensaje.set(null);
    this.reservaService.cancelarReserva(id, 'Cancelado por el cliente').subscribe({
      next: () => this.cargar(),
      error: (err) => {
        this.errorMensaje.set(extraerMensajeErrorReserva(err));
      },
    });
  }
}
