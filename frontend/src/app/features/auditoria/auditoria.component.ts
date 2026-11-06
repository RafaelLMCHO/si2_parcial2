import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-auditoria',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="auditoria-page">
      <h2>Bitácora de Auditoría (CU-05)</h2>
      <p class="subtitle">Registro inmutable de trazabilidad y operaciones del sistema (BR-13 / BR-14).</p>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Fecha y Hora</th>
              <th>Actor</th>
              <th>Acción</th>
              <th>Entidad</th>
              <th>ID Entidad</th>
              <th>IP Origen</th>
              <th>Superadmin</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let ev of eventos">
              <td>{{ ev.ocurrido_en | date:'short' }}</td>
              <td><code>{{ ev.actor_tipo }}</code></td>
              <td><span class="badge" [ngClass]="'badge-' + ev.accion">{{ ev.accion }}</span></td>
              <td>{{ ev.entidad }}</td>
              <td><small>{{ ev.entidad_id || 'N/A' }}</small></td>
              <td>{{ ev.ip_origen || '127.0.0.1' }}</td>
              <td>
                <span *ngIf="ev.es_accion_superadmin" class="tag-superadmin">Superadmin</span>
                <span *ngIf="!ev.es_accion_superadmin" class="tag-tenant">Tenant</span>
              </td>
            </tr>
            <tr *ngIf="eventos.length === 0">
              <td colspan="7" class="text-center">No hay registros de auditoría disponibles.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .auditoria-page { padding: 24px; font-family: inherit; }
    .subtitle { color: #64748b; font-size: 0.9rem; margin-bottom: 20px; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; font-weight: 600; color: #475569; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; }
    .badge-insert { background: #dcfce7; color: #166534; }
    .badge-update { background: #fef3c7; color: #b45309; }
    .badge-delete { background: #fee2e2; color: #991b1b; }
    .tag-superadmin { background: #e0e7ff; color: #3730a3; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; }
    .tag-tenant { color: #64748b; font-size: 0.75rem; }
  `]
})
export class AuditoriaComponent implements OnInit {
  eventos: any[] = [];

  constructor(private readonly http: HttpClient) {}

  ngOnInit(): void {
    this.http.get<any>(`${environment.apiUrl}/saas/auditoria`).subscribe({
      next: (resp) => (this.eventos = resp.items || []),
      error: () => (this.eventos = []),
    });
  }
}

