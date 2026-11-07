import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-empleados',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="empleados-page">
      <div class="header">
        <h2>Gestión de Usuarios y Roles (CU-10)</h2>
        <button class="btn btn-primary" (click)="abrirModal()">+ Nuevo Usuario</button>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Correo</th>
              <th>Rol</th>
              <th>Sucursal</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let emp of empleados">
              <td><strong>{{ emp.nombre }}</strong></td>
              <td>{{ emp.correo }}</td>
              <td><span class="role-badge">{{ emp.rol_nombre || emp.rol }}</span></td>
              <td>{{ emp.sucursal_nombre || 'Todas / Matriz' }}</td>
              <td>
                <span class="badge" [class.badge-success]="emp.estado === 'activo'" [class.badge-danger]="emp.estado !== 'activo'">
                  {{ emp.estado }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal Crear Usuario -->
      <div class="modal-backdrop" *ngIf="mostrarModal">
        <div class="modal-card">
          <h3>Registrar Usuario / Empleado</h3>
          <form [formGroup]="form" (ngSubmit)="guardar()">
            <div class="form-group">
              <label>Nombre Completo</label>
              <input formControlName="nombre" class="form-control" />
            </div>
            <div class="form-group">
              <label>Correo Electrónico</label>
              <input type="email" formControlName="correo" class="form-control" />
            </div>
            <div class="form-group">
              <label>Rol</label>
              <select formControlName="rol_id" class="form-control">
                <option value="11111111-1111-1111-1111-111111111201">Administrador de Empresa</option>
                <option value="11111111-1111-1111-1111-111111111204">Encargado de Sucursal</option>
                <option value="11111111-1111-1111-1111-111111111202">Cajero</option>
              </select>
            </div>
            <div class="form-group">
              <label>Contraseña Provisional</label>
              <input type="password" formControlName="password" class="form-control" />
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
    .empleados-page { padding: 24px; font-family: inherit; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: 500; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-outline { background: #fff; border: 1px solid #cbd5e1; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; font-weight: 600; color: #475569; }
    .role-badge { background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; text-transform: uppercase; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 400px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.82rem; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class EmpleadosComponent implements OnInit {
  empleados: any[] = [];
  mostrarModal = false;
  form: FormGroup;

  constructor(private readonly http: HttpClient, private readonly fb: FormBuilder) {
    this.form = this.fb.group({
      nombre: ['', Validators.required],
      correo: ['', [Validators.required, Validators.email]],
      rol_id: ['11111111-1111-1111-1111-111111111202', Validators.required],
      password: ['ClaveSegura123!', Validators.required],
    });
  }

  ngOnInit(): void {
    this.cargarEmpleados();
  }

  cargarEmpleados(): void {
    this.http.get<any>(`${environment.apiUrl}/empleados`).subscribe({
      next: (resp) => (this.empleados = resp.items || []),
      error: () => (this.empleados = []),
    });
  }

  abrirModal(): void {
    this.mostrarModal = true;
  }

  guardar(): void {
    this.http.post(`${environment.apiUrl}/empleados`, this.form.value).subscribe({
      next: () => {
        this.mostrarModal = false;
        this.cargarEmpleados();
      },
    });
  }
}

