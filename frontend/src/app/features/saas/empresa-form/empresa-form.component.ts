import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { apiErrorMessage, isNetworkError } from '../../../core/error-mapper';
import { EmpresaCreateResponse } from '../../../core/models';
import { NetworkService } from '../../../core/network.service';
import { SaasService } from '../../../core/saas.service';

@Component({
  selector: 'app-empresa-form',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './empresa-form.component.html',
  styleUrl: './empresa-form.component.css',
})
export class EmpresaFormComponent {
  private readonly fb = inject(FormBuilder);
  private readonly saas = inject(SaasService);
  readonly network = inject(NetworkService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<EmpresaCreateResponse | null>(null);
  readonly copied = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    nit: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(20)]],
    telefono: ['', [Validators.maxLength(20)]],
    direccion: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(200)]],
    correo_admin: ['', [Validators.required, Validators.email, Validators.maxLength(254)]],
    nombre_admin: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (!this.network.online()) {
      this.error.set('Sin conexion. Registre empresas cuando recupere la red.');
      return;
    }

    const raw = this.form.getRawValue();
    this.loading.set(true);
    this.error.set(null);
    this.saas
      .createEmpresa({
        nombre: raw.nombre.trim(),
        nit: raw.nit.trim().toUpperCase(),
        telefono: raw.telefono.trim() || null,
        direccion: raw.direccion.trim(),
        correo_admin: raw.correo_admin.trim().toLowerCase(),
        nombre_admin: raw.nombre_admin.trim(),
      })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.result.set(response);
          this.copied.set(false);
          this.form.reset();
        },
        error: (error) => {
          this.error.set(
            isNetworkError(error)
              ? 'Sin conexion. No se registro la empresa.'
              : apiErrorMessage(error, 'No se pudo registrar la empresa.'),
          );
        },
      });
  }

  async copyPassword(): Promise<void> {
    const result = this.result();
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.password_temporal);
      this.copied.set(true);
    } catch {
      this.copied.set(false);
    }
  }

  registerAnother(): void {
    this.result.set(null);
    this.error.set(null);
    this.copied.set(false);
  }
}
