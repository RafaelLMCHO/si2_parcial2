import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-sucursales',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="sucursales-page">
      <div class="header">
        <div>
          <h2>Gestión de Sucursales (CU-11)</h2>
          <p class="subtitle" *ngIf="limitePlan">
            Sucursales activas: {{ limitePlan.activas }} de {{ limitePlan.limite }} permitidas por el plan (BR-02).
          </p>
        </div>
        <button class="btn btn-primary" (click)="abrirModal()">+ Nueva Sucursal</button>
      </div>

      <div *ngIf="mensajeError" class="alert alert-error">{{ mensajeError }}</div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Dirección</th>
              <th>Ciudad</th>
              <th>Teléfono</th>
              <th>Tipo</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let s of sucursales">
              <td><strong>{{ s.nombre }}</strong></td>
              <td>{{ s.direccion }}</td>
              <td>{{ s.ciudad_nombre }}</td>
              <td>{{ s.telefono || 'N/A' }}</td>
              <td>
                <span *ngIf="s.es_matriz" class="badge-matriz">Matriz</span>
                <span *ngIf="!s.es_matriz">Filial</span>
              </td>
              <td>
                <span class="badge" [class.badge-success]="s.estado === 'activa'" [class.badge-danger]="s.estado !== 'activa'">
                  {{ s.estado }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal Crear Sucursal -->
      <div class="modal-backdrop" *ngIf="mostrarModal">
        <div class="modal-card">
          <h3>Dar de Alta Sucursal</h3>
          <form [formGroup]="form" (ngSubmit)="guardar()">
            <div class="form-group">
              <label>Nombre de Sucursal</label>
              <input formControlName="nombre" class="form-control" />
            </div>
            <div class="form-group">
              <label>Dirección</label>
              <input formControlName="direccion" class="form-control" />
            </div>
            <div class="form-group">
              <label>ID de Ciudad</label>
              <input type="number" formControlName="ciudad_id" class="form-control" />
            </div>
            <div class="form-group">
              <label>Teléfono</label>
              <input formControlName="telefono" class="form-control" />
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-outline" (click)="mostrarModal = false">Cancelar</button>
              <button type="submit" class="btn btn-primary" [disabled]="form.invalid">Guardar</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .sucursales-page { padding: 24px; font-family: inherit; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .subtitle { color: #64748b; font-size: 0.88rem; margin: 4px 0 0 0; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: 500; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-outline { background: #fff; border: 1px solid #cbd5e1; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; font-weight: 600; color: #475569; }
    .badge-matriz { background: #fef3c7; color: #b45309; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; text-transform: uppercase; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .alert-error { background: #fee2e2; color: #991b1b; padding: 10px; border-radius: 6px; margin-bottom: 14px; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 400px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.82rem; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class SucursalesComponent implements OnInit {
  sucursales: any[] = [];
  limitePlan: any = null;
  mostrarModal = false;
  mensajeError = '';
  form: FormGroup;

  constructor(private readonly http: HttpClient, private readonly fb: FormBuilder) {
    this.form = this.fb.group({
      nombre: ['', Validators.required],
      direccion: ['', Validators.required],
      ciudad_id: [1, Validators.required],
      telefono: [''],
    });
  }

  ngOnInit(): void {
    this.cargarSucursales();
  }

  cargarSucursales(): void {
    this.http.get<any>(`${environment.apiUrl}/sucursales`).subscribe({
      next: (resp) => {
        this.sucursales = resp.items || [];
        this.limitePlan = resp.limite_plan;
      },
    });
  }

  abrirModal(): void {
    this.mensajeError = '';
    this.mostrarModal = true;
  }

  guardar(): void {
    this.http.post(`${environment.apiUrl}/sucursales`, this.form.value).subscribe({
      next: () => {
        this.mostrarModal = false;
        this.cargarSucursales();
      },
      error: (err) => {
        this.mensajeError = err?.error?.detail?.message || 'Error al crear sucursal (Compruebe límite de plan BR-02)';
      },
    });
  }
}

