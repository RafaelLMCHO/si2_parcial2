import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/auth.service';
import { apiErrorMessage } from '../../../core/error-mapper';
import { NetworkService } from '../../../core/network.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly network = inject(NetworkService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly showPassword = signal(false);

  readonly form = this.fb.nonNullable.group({
    empresa_slug: [this.auth.tenantSlug()],
    correo: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    if (!this.network.online()) {
      this.error.set('Sin conexion. Inicie sesion cuando recupere la red.');
      return;
    }

    const raw = this.form.getRawValue();
    this.loading.set(true);
    this.error.set(null);
    this.auth
      .login({
        ...raw,
        empresa_slug: raw.empresa_slug.trim() || null,
      })
      .subscribe({
        next: () => {
          const user = this.auth.user();
          const target =
            user?.rol === 'superadmin' && !user.empresa_id ? '/saas' : '/profile';
          void this.router.navigateByUrl(target);
        },
        error: (error) => {
          this.error.set(apiErrorMessage(error, 'No se pudo iniciar sesion. Verifique sus datos.'));
          this.loading.set(false);
        },
        complete: () => this.loading.set(false),
      });
  }
}
