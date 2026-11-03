import { DatePipe, DecimalPipe, KeyValuePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize, forkJoin } from 'rxjs';

import { apiErrorMessage, isNetworkError } from '../../../core/error-mapper';
import { EmpresaResumen, Plan } from '../../../core/models';
import { NetworkService } from '../../../core/network.service';
import { SaasService } from '../../../core/saas.service';

@Component({
  selector: 'app-empresa-detail',
  imports: [ReactiveFormsModule, RouterLink, DatePipe, DecimalPipe, KeyValuePipe],
  templateUrl: './empresa-detail.component.html',
  styleUrl: './empresa-detail.component.css',
})
export class EmpresaDetailComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly saas = inject(SaasService);
  private readonly route = inject(ActivatedRoute);
  readonly network = inject(NetworkService);

  private readonly empresaId = this.route.snapshot.paramMap.get('id') ?? '';

  readonly empresa = signal<EmpresaResumen | null>(null);
  readonly planes = signal<Plan[]>([]);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  readonly confirmingSuspend = signal(false);

  readonly planForm = this.fb.nonNullable.group({
    plan_codigo: ['', [Validators.required]],
    fecha_inicio: [todayIso(), [Validators.required]],
    fecha_fin: [plusDaysIso(30), [Validators.required]],
    estado: ['activa', [Validators.required]],
    renovacion_auto: [false],
  });

  readonly accionForm = this.fb.nonNullable.group({
    motivo: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    if (!this.empresaId) {
      this.error.set('Empresa no identificada.');
      return;
    }
    if (!this.network.online()) {
      this.error.set('Sin conexion. La gestion SaaS requiere red.');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    forkJoin({
      empresa: this.saas.getEmpresa(this.empresaId),
      planes: this.saas.listPlanes(),
    })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: ({ empresa, planes }) => {
          this.planes.set(planes);
          this.applyEmpresa(empresa);
        },
        error: (error) => this.error.set(apiErrorMessage(error, 'No se pudo cargar la empresa.')),
      });
  }

  assignPlan(): void {
    if (this.planForm.invalid) {
      this.planForm.markAllAsTouched();
      return;
    }
    if (!this.network.online()) {
      this.error.set('Sin conexion. No se puede asignar el plan.');
      return;
    }

    const raw = this.planForm.getRawValue();
    this.saving.set(true);
    this.error.set(null);
    this.message.set(null);
    this.saas
      .assignSuscripcion(this.empresaId, {
        plan_codigo: raw.plan_codigo,
        fecha_inicio: raw.fecha_inicio,
        fecha_fin: raw.fecha_fin,
        estado: raw.estado,
        renovacion_auto: raw.renovacion_auto,
      })
      .pipe(finalize(() => this.saving.set(false)))
      .subscribe({
        next: (response) => {
          this.message.set(
            `Plan ${response.suscripcion.plan.nombre} asignado en estado ${response.suscripcion.estado}.`,
          );
          this.load();
        },
        error: (error) => {
          this.error.set(
            isNetworkError(error)
              ? 'Sin conexion. No se guardo la suscripcion.'
              : apiErrorMessage(error, 'No se pudo asignar el plan.'),
          );
        },
      });
  }

  suspender(): void {
    if (!this.network.online()) {
      this.error.set('Sin conexion. No se puede suspender el servicio.');
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    this.message.set(null);
    const motivo = this.accionForm.controls.motivo.value.trim() || null;
    this.saas
      .suspenderEmpresa(this.empresaId, motivo)
      .pipe(finalize(() => this.saving.set(false)))
      .subscribe({
        next: (response) => {
          this.confirmingSuspend.set(false);
          this.message.set(response.mensaje);
          this.load();
        },
        error: (error) => {
          this.error.set(apiErrorMessage(error, 'No se pudo suspender el servicio.'));
        },
      });
  }

  reactivar(): void {
    if (!this.network.online()) {
      this.error.set('Sin conexion. No se puede reactivar el servicio.');
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    this.message.set(null);
    const motivo = this.accionForm.controls.motivo.value.trim() || null;
    this.saas
      .reactivarEmpresa(this.empresaId, motivo)
      .pipe(finalize(() => this.saving.set(false)))
      .subscribe({
        next: (response) => {
          this.message.set(response.mensaje);
          this.load();
        },
        error: (error) => {
          this.error.set(apiErrorMessage(error, 'No se pudo reactivar el servicio.'));
        },
      });
  }

  limiteLabel(recurso: string): string {
    const labels: Record<string, string> = {
      sucursales: 'Sucursales',
      usuarios: 'Usuarios',
      productos: 'Productos',
      consultas_ia_mes: 'Consultas IA / mes',
    };
    return labels[recurso] ?? recurso;
  }

  private applyEmpresa(empresa: EmpresaResumen): void {
    this.empresa.set(empresa);
    const actual = empresa.suscripcion;
    if (actual) {
      this.planForm.patchValue({
        plan_codigo: actual.plan.codigo,
        fecha_inicio: actual.fecha_inicio,
        fecha_fin: actual.fecha_fin ?? plusDaysIso(30),
        estado: actual.estado === 'cancelada' ? 'activa' : actual.estado,
        renovacion_auto: actual.renovacion_auto,
      });
    } else if (this.planes().length) {
      this.planForm.patchValue({
        plan_codigo: this.planes()[0].codigo,
        fecha_inicio: todayIso(),
        fecha_fin: plusDaysIso(30),
        estado: 'activa',
      });
    }
  }
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function plusDaysIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}
