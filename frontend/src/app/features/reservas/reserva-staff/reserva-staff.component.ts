import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../../core/auth.service';
import { ReservaService } from '../../../core/reserva.service';
import { extraerMensajeErrorReserva } from '../reserva-creacion/reserva-creacion.component';

@Component({
  selector: 'app-reserva-staff',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="rs-page">
      <div class="rs-tabs">
        <a routerLink="/reservas/nueva" class="rs-tab">CU-19: Crear Reserva (Probador)</a>
        <a routerLink="/reservas/mis-reservas" class="rs-tab">CU-20: Mis Reservas / Consulta</a>
        @if (esStaff()) {
          <a routerLink="/reservas/staff" class="rs-tab active">CU-21: Preparación Staff Tienda</a>
        }
      </div>

      <header class="rs-header">
        <div>
          <span class="rs-badge-tag">Operaciones en Tienda</span>
          <h1 class="rs-title">CU-21: Validación y Preparación de Reservas (Staff)</h1>
          <p class="rs-subtitle">Módulo de tienda para apartar prendas en probador y registrar entrega</p>
        </div>
        @if (esStaff()) {
          <button type="button" (click)="cargar()" class="rs-btn rs-btn-ghost">
            Actualizar
          </button>
        }
      </header>

      @if (!esStaff()) {
        <div class="rs-banner warning">
          Esta vista está reservada para el personal de tienda (Encargado / Cajero / Administrador).
          <a routerLink="/reservas/mis-reservas" class="rs-inline-link">Ir a Mis Reservas (CU-20)</a>
        </div>
      } @else {
        @if (mensaje()) {
          <div class="rs-banner" [class.error]="esError()" [class.success]="!esError()" role="alert">
            {{ mensaje() }}
          </div>
        }

        @if (cargando()) {
          <div class="rs-loading">
            <div class="rs-spinner"></div>
            <span>Cargando bandeja de preparación...</span>
          </div>
        } @else {
          <div class="rs-table-card">
            <div class="rs-table-scroll">
              <table class="rs-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Cliente</th>
                    <th>Fecha Visita</th>
                    <th>Probador</th>
                    <th>Estado</th>
                    <th class="right">Acciones Staff</th>
                  </tr>
                </thead>
                <tbody>
                  @for (r of reservas(); track r.id) {
                    <tr>
                      <td class="mono code">{{ r.codigo || r.id.slice(0, 8) }}</td>
                      <td>{{ r.cliente_email || r.usuario_id || 'Cliente' }}</td>
                      <td class="muted">{{ r.fecha_visita | date:'short' }}</td>
                      <td>
                        <span [class.prob-yes]="r.probador" [class.muted]="!r.probador">
                          {{ r.probador ? (r.probador === true ? 'Sí' : r.probador) : 'No' }}
                        </span>
                      </td>
                      <td>
                        <span class="rs-status">{{ r.estado }}</span>
                      </td>
                      <td class="right actions-cell">
                        <button type="button" (click)="preparar(r.id)" class="rs-act rs-act-prep">
                          Preparar
                        </button>
                        <button type="button" (click)="completar(r.id)" class="rs-act rs-act-done">
                          Entregar
                        </button>
                      </td>
                    </tr>
                  } @empty {
                    <tr>
                      <td colspan="6" class="rs-empty-cell">No hay reservas pendientes en la sucursal.</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .rs-page {
      max-width: 1080px;
      margin: 0 auto;
      padding: 24px 16px 40px;
      color: #0f172a;
    }
    .rs-tabs {
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
    .rs-tab {
      padding: 0.45rem 0.9rem;
      border-radius: 9px;
      font-size: 0.86rem;
      font-weight: 600;
      color: #475569;
      text-decoration: none;
    }
    .rs-tab:hover { background: #f8fafc; color: #0f172a; }
    .rs-tab.active { background: #fdf2f8; color: #be185d; font-weight: 700; }
    .rs-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .rs-badge-tag {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #4338ca;
      background: #eef2ff;
      border: 1px solid #c7d2fe;
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      margin-bottom: 0.45rem;
    }
    .rs-title { font-size: 1.6rem; font-weight: 800; margin: 0 0 0.25rem; }
    .rs-subtitle { margin: 0; font-size: 0.9rem; color: #64748b; }
    .rs-btn {
      padding: 0.5rem 0.95rem;
      border-radius: 10px;
      font-size: 0.84rem;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #334155;
    }
    .rs-btn:hover { background: #f8fafc; }
    .rs-banner {
      padding: 0.85rem 1rem;
      border-radius: 12px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 1rem;
      border: 1px solid transparent;
    }
    .rs-banner.warning { background: #fffbeb; border-color: #fde68a; color: #92400e; }
    .rs-banner.error { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
    .rs-banner.success { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
    .rs-inline-link { margin-left: 0.5rem; font-weight: 700; text-decoration: underline; color: inherit; }
    .rs-loading {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 0.75rem;
      padding: 2.5rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      color: #64748b;
    }
    .rs-spinner {
      width: 24px;
      height: 24px;
      border: 3px solid #e2e8f0;
      border-top-color: #be185d;
      border-radius: 50%;
      animation: rs-spin 0.8s linear infinite;
    }
    @keyframes rs-spin { to { transform: rotate(360deg); } }
    .rs-table-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
      overflow: hidden;
    }
    .rs-table-scroll { overflow-x: auto; }
    .rs-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem; }
    .rs-table thead th {
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
      padding: 0.8rem 1rem;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #64748b;
      font-weight: 700;
    }
    .rs-table tbody td {
      padding: 0.9rem 1rem;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }
    .rs-table tbody tr:hover { background: #f8fafc; }
    .right { text-align: right; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .code { font-weight: 700; color: #4338ca; }
    .muted { color: #64748b; }
    .prob-yes { color: #7e22ce; font-weight: 700; }
    .rs-status {
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.74rem;
      font-weight: 700;
      background: #f1f5f9;
      color: #334155;
    }
    .actions-cell { white-space: nowrap; display: flex; justify-content: flex-end; gap: 0.45rem; }
    .rs-act {
      padding: 0.35rem 0.7rem;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 700;
      border: 0;
      cursor: pointer;
    }
    .rs-act-prep { background: #eef2ff; color: #3730a3; }
    .rs-act-prep:hover { background: #e0e7ff; }
    .rs-act-done { background: #dcfce7; color: #166534; }
    .rs-act-done:hover { background: #bbf7d0; }
    .rs-empty-cell { padding: 2.5rem; text-align: center; color: #64748b; }
  `],
})
export class ReservaStaffComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly reservaService = inject(ReservaService);

  esStaff = computed(() =>
    ['superadmin', 'administrador', 'encargado', 'cajero'].includes(this.auth.user()?.rol || ''),
  );

  cargando = signal(false);
  reservas = signal<any[]>([]);
  mensaje = signal<string | null>(null);
  esError = signal(false);

  ngOnInit() {
    if (this.esStaff()) {
      this.cargar();
    }
  }

  cargar() {
    this.cargando.set(true);
    this.reservaService.listarReservas().subscribe({
      next: (res: any) => {
        this.reservas.set(res.items || []);
        this.cargando.set(false);
      },
      error: (err) => {
        this.esError.set(true);
        this.mensaje.set(extraerMensajeErrorReserva(err));
        this.cargando.set(false);
      },
    });
  }

  preparar(id: string) {
    this.mensaje.set(null);
    this.reservaService.prepararReserva(id).subscribe({
      next: () => {
        this.esError.set(false);
        this.mensaje.set('Reserva marcada como preparada.');
        this.cargar();
      },
      error: (err) => {
        this.esError.set(true);
        this.mensaje.set(extraerMensajeErrorReserva(err));
      },
    });
  }

  completar(id: string) {
    this.mensaje.set(null);
    this.reservaService.completarReserva(id).subscribe({
      next: () => {
        this.esError.set(false);
        this.mensaje.set('Reserva entregada y completada correctamente.');
        this.cargar();
      },
      error: (err) => {
        this.esError.set(true);
        this.mensaje.set(extraerMensajeErrorReserva(err));
      },
    });
  }
}
