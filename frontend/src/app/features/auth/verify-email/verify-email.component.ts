import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/auth.service';
import { apiErrorMessage } from '../../../core/error-mapper';
import { NetworkService } from '../../../core/network.service';

@Component({
  selector: 'app-verify-email',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './verify-email.component.html',
  styleUrl: './verify-email.component.css',
})
export class VerifyEmailComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  readonly network = inject(NetworkService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    empresa_slug: [this.auth.tenantSlug(), [Validators.required]],
    token: ['', [Validators.required, Validators.minLength(20)]],
  });

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    this.form.patchValue({
      empresa_slug: params.get('empresa_slug') ?? this.auth.tenantSlug(),
      token: params.get('token') ?? '',
    });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    if (!this.network.online()) {
      this.error.set('Sin conexion. La verificacion necesita red.');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    this.auth.verifyEmail(this.form.getRawValue()).subscribe({
      next: (response) => this.success.set(response.mensaje),
      error: (error) => {
        this.error.set(apiErrorMessage(error, 'No se pudo verificar el correo.'));
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }
}
