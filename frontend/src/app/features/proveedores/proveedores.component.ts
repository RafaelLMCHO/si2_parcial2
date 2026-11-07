import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-proveedores',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="proveedores-page">
      <div class="header">
        <h2>Gestión de Proveedores Textiles (CU-15)</h2>
        <button class="btn btn-primary" (click)="abrirModal()">+ Nuevo Proveedor</button>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Razón Social</th>
              <th>NIT</th>
              <th>Correo</th>
              <th>Teléfono</th>
              <th>Contacto</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of proveedores">
              <td><strong>{{ p.nombre }}</strong></td>
              <td><code>{{ p.nit }}</code></td>
              <td>{{ p.correo }}</td>
              <td>{{ p.telefono || 'N/A' }}</td>
              <td>{{ p.contacto_nombre || 'Principal' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal Crear Proveedor -->
      <div class="modal-backdrop" *ngIf="mostrarModal">
        <div class="modal-card">
          <h3>Registrar Proveedor Textil</h3>
          <form [formGroup]="form" (ngSubmit)="guardar()">
            <div class="form-group">
              <label>Razón Social / Nombre</label>
              <input formControlName="nombre" class="form-control" />
            </div>
            <div class="form-group">
              <label>NIT / Identificación Fiscal</label>
              <input formControlName="nit" class="form-control" />
            </div>
            <div class="form-group">
              <label>Correo Electrónico</label>
              <input type="email" formControlName="correo" class="form-control" />
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
    .proveedores-page { padding: 24px; font-family: inherit; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: 500; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-outline { background: #fff; border: 1px solid #cbd5e1; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; font-weight: 600; color: #475569; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 400px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.82rem; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class ProveedoresComponent implements OnInit {
  proveedores: any[] = [];
  mostrarModal = false;
  form: FormGroup;

  constructor(private readonly http: HttpClient, private readonly fb: FormBuilder) {
    this.form = this.fb.group({
      nombre: ['', Validators.required],
      nit: ['', Validators.required],
      correo: ['', [Validators.required, Validators.email]],
      telefono: [''],
    });
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.http.get<any>(`${environment.apiUrl}/proveedores`).subscribe({
      next: (resp) => (this.proveedores = resp.items || []),
      error: () => (this.proveedores = []),
    });
  }

  abrirModal(): void {
    this.mostrarModal = true;
  }

  guardar(): void {
    this.http.post(`${environment.apiUrl}/proveedores`, this.form.value).subscribe({
      next: () => {
        this.mostrarModal = false;
        this.cargar();
      },
    });
  }
}

