import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-catalogo-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="catalogo-admin-page">
      <div class="header">
        <h2>Catálogo de Prendas y Variantes SKU (CU-12)</h2>
        <button class="btn btn-primary" (click)="abrirModal()">+ Nueva Prenda</button>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Código Estilo</th>
              <th>Nombre</th>
              <th>Categoría</th>
              <th>Precio Base</th>
              <th>Variantes (SKU)</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of prendas">
              <td><code>{{ p.codigo }}</code></td>
              <td><strong>{{ p.nombre }}</strong></td>
              <td>{{ p.categoria_nombre || 'General' }}</td>
              <td>{{ p.precio_base | currency:'BOB ':'symbol':'1.2-2' }}</td>
              <td>
                <span class="badge-sku">{{ p.variantes?.length || 0 }} SKU(s)</span>
              </td>
              <td>
                <span class="badge" [class.badge-success]="p.estado === 'activa'" [class.badge-danger]="p.estado !== 'activa'">
                  {{ p.estado }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal Crear Prenda -->
      <div class="modal-backdrop" *ngIf="mostrarModal">
        <div class="modal-card">
          <h3>Registrar Nueva Prenda en Catálogo</h3>
          <form [formGroup]="form" (ngSubmit)="guardar()">
            <div class="form-group">
              <label>Código de Estilo</label>
              <input formControlName="codigo" class="form-control" placeholder="Ej: FS-CAS-001" />
            </div>
            <div class="form-group">
              <label>Nombre de la Prenda</label>
              <input formControlName="nombre" class="form-control" />
            </div>
            <div class="form-group">
              <label>Precio Base</label>
              <input type="number" formControlName="precio_base" class="form-control" />
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-outline" (click)="mostrarModal = false">Cancelar</button>
              <button type="submit" class="btn btn-primary" [disabled]="form.invalid">Guardar Prenda</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .catalogo-admin-page { padding: 24px; font-family: inherit; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: 500; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-outline { background: #fff; border: 1px solid #cbd5e1; }
    .table-container { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left; }
    .data-table th, .data-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
    .data-table th { background: #f8fafc; font-weight: 600; color: #475569; }
    .badge-sku { background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; text-transform: uppercase; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 420px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.82rem; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class CatalogoAdminComponent implements OnInit {
  prendas: any[] = [];
  mostrarModal = false;
  form: FormGroup;

  constructor(private readonly http: HttpClient, private readonly fb: FormBuilder) {
    this.form = this.fb.group({
      codigo: ['', Validators.required],
      nombre: ['', Validators.required],
      precio_base: [100, [Validators.required, Validators.min(0)]],
    });
  }

  ngOnInit(): void {
    this.cargarCatalogo();
  }

  cargarCatalogo(): void {
    this.http.get<any>(`${environment.apiUrl}/catalogo/admin/prendas`).subscribe({
      next: (resp) => (this.prendas = resp.items || []),
      error: () => (this.prendas = []),
    });
  }

  abrirModal(): void {
    this.mostrarModal = true;
  }

  guardar(): void {
    this.http.post(`${environment.apiUrl}/catalogo/admin/prendas`, this.form.value).subscribe({
      next: () => {
        this.mostrarModal = false;
        this.cargarCatalogo();
      },
    });
  }
}

