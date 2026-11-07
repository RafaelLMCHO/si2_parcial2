import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-temporadas',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="temporadas-page">
      <div class="header">
        <h2>Temporadas y Colecciones Comerciales (CU-16)</h2>
        <button class="btn btn-primary" (click)="abrirModal()">+ Nueva Colección</button>
      </div>

      <div class="grid-layout">
        <!-- Colecciones -->
        <div class="card">
          <h3>Colecciones</h3>
          <ul class="list">
            <li *ngFor="let c of colecciones">
              <strong>{{ c.nombre }}</strong>
              <span class="badge-year">{{ c.anio || '2026' }}</span>
            </li>
          </ul>
        </div>

        <!-- Temporadas -->
        <div class="card">
          <h3>Temporadas</h3>
          <ul class="list">
            <li *ngFor="let t of temporadas">
              <strong>{{ t.nombre }}</strong>
              <small>{{ t.fecha_inicio | date:'mediumDate' }} - {{ t.fecha_fin | date:'mediumDate' }}</small>
            </li>
          </ul>
        </div>
      </div>

      <!-- Modal Crear Colección -->
      <div class="modal-backdrop" *ngIf="mostrarModal">
        <div class="modal-card">
          <h3>Crear Colección</h3>
          <form [formGroup]="form" (ngSubmit)="guardar()">
            <div class="form-group">
              <label>Nombre de la Colección</label>
              <input formControlName="nombre" class="form-control" placeholder="Ej: Esenciales Verano" />
            </div>
            <div class="form-group">
              <label>Año</label>
              <input type="number" formControlName="anio" class="form-control" />
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
    .temporadas-page { padding: 24px; font-family: inherit; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-weight: 500; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-outline { background: #fff; border: 1px solid #cbd5e1; }
    .grid-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
    .card h3 { margin-top: 0; font-size: 1.1rem; color: #1e293b; }
    .list { list-style: none; padding: 0; margin: 0; }
    .list li { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
    .badge-year { background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-card { background: #fff; padding: 24px; border-radius: 8px; width: 380px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 0.82rem; margin-bottom: 4px; }
    .form-control { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  `]
})
export class TemporadasComponent implements OnInit {
  colecciones: any[] = [];
  temporadas: any[] = [];
  mostrarModal = false;
  form: FormGroup;

  constructor(private readonly http: HttpClient, private readonly fb: FormBuilder) {
    this.form = this.fb.group({
      nombre: ['', Validators.required],
      anio: [2026, Validators.required],
    });
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.http.get<any>(`${environment.apiUrl}/colecciones`).subscribe({
      next: (resp) => (this.colecciones = resp.items || []),
      error: () => (this.colecciones = []),
    });
    this.http.get<any>(`${environment.apiUrl}/colecciones/temporadas`).subscribe({
      next: (resp) => (this.temporadas = resp.items || []),
      error: () => (this.temporadas = []),
    });
  }

  abrirModal(): void {
    this.mostrarModal = true;
  }

  guardar(): void {
    this.http.post(`${environment.apiUrl}/colecciones`, this.form.value).subscribe({
      next: () => {
        this.mostrarModal = false;
        this.cargar();
      },
    });
  }
}

