import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/error-mapper';
import { PagoService } from '../../core/pago.service';

@Component({
  selector: 'app-pagos',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="pagos-page">
      <h2>Gestión y Conciliación de Pagos (CU-24)</h2>
      <p class="subtitle">Monitoreo de transacciones con Stripe Sandbox y Webhooks.</p>

      <div class="stripe-badge-box">
        <span class="badge-status">Stripe Sandbox Activo</span>
        <p>Moneda de cobro: <strong>BOB / USD</strong> • Webhook con verificación de firma HMAC-SHA256.</p>
      </div>

      <div *ngIf="errorMsg" class="alert-error">⚠️ {{ errorMsg }}</div>
      <div *ngIf="okMsg" class="alert-ok">✓ {{ okMsg }}</div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID Pago</th>
              <th>Monto</th>
              <th>Método</th>
              <th>Pasarela ID</th>
              <th>Referencia / Cargo</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of pagos">
              <td><code>{{ p.id }}</code></td>
              <td><strong>{{ p.monto | currency:'BOB ':'symbol':'1.2-2' }}</strong></td>
              <td>{{ p.metodo }}</td>
              <td><small>{{ p.pasarela_id || 'N/A' }}</small></td>
              <td>{{ p.referencia || 'N/A' }}</td>
              <td>
                <span
                  class="badge"
                  [class.badge-success]="p.estado === 'completado'"
                  [class.badge-pending]="p.estado === 'pendiente'"
                  [class.badge-danger]="p.estado === 'fallido'"
                >
                  {{ p.estado }}
                </span>
              </td>
              <td>
                <button
                  *ngIf="p.estado === 'pendiente' && p.pasarela_id"
                  type="button"
                  class="btn-conciliar"
                  [disabled]="conciliandoId === p.id"
                  (click)="conciliar(p.id)"
                >
                  {{ conciliandoId === p.id ? 'Conciliando...' : 'Confirmar / Conciliar' }}
                </button>
              </td>
            </tr>
            <tr *ngIf="pagos.length === 0">
              <td colspan="7" class="text-center">No hay registros de pagos recientes.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .pagos-page { padding: 24px; font-family: inherit; }
    .subtitle { color: #64748b; font-size: 0.9rem; margin-bottom: 20px; }
    .stripe-badge-box { background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 14px; margin-bottom: 20px; }
    .badge-status { background: #4f46e5; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }
    .stripe-badge-box p { margin: 8px 0 0 0; font-size: 0.88rem; color: #3730a3; }
    .alert-error { background: #fee2e2; color: #991b1b; padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; }
    .alert-ok { background: #dcfce7; color: #166534; padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; font-weight: 600; color: #475569; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; text-transform: uppercase; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-pending { background: #fef3c7; color: #92400e; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .btn-conciliar { background: #4f46e5; color: #fff; border: none; border-radius: 6px; padding: 5px 10px; font-size: 0.78rem; cursor: pointer; }
    .btn-conciliar:disabled { opacity: 0.6; cursor: not-allowed; }
  `]
})
export class PagosComponent implements OnInit {
  pagos: any[] = [];
  conciliandoId = '';
  errorMsg = '';
  okMsg = '';

  constructor(
    private readonly http: HttpClient,
    private readonly pagoService: PagoService
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.http.get<any>(`${environment.apiUrl}/pagos`).subscribe({
      next: (resp) => (this.pagos = Array.isArray(resp) ? resp : (resp.items || [])),
      error: (err) => {
        this.pagos = [];
        this.errorMsg = apiErrorMessage(err, 'No se pudo cargar la lista de pagos.');
      },
    });
  }

  conciliar(pagoId: string): void {
    this.conciliandoId = pagoId;
    this.errorMsg = '';
    this.okMsg = '';
    this.pagoService.conciliarPago(pagoId, 'pm_card_visa').subscribe({
      next: (estado) => {
        this.conciliandoId = '';
        this.okMsg = `Pago conciliado (estado: ${estado.pago_estado || estado.venta_estado}).`;
        this.cargar();
      },
      error: (err) => {
        this.conciliandoId = '';
        this.errorMsg = apiErrorMessage(err, 'No se pudo conciliar el pago con Stripe.');
      },
    });
  }
}

