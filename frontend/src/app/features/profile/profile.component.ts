import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AuthService } from '../../core/auth.service';
import { apiErrorMessage, isNetworkError } from '../../core/error-mapper';
import { InstallService } from '../../core/install.service';
import { LogoutDialogComponent } from '../../core/logout-dialog.component';
import { User } from '../../core/models';
import { NetworkService } from '../../core/network.service';

@Component({
  selector: 'app-profile',
  imports: [ReactiveFormsModule, DatePipe, LogoutDialogComponent],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css',
})
export class ProfileComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  readonly auth = inject(AuthService);
  readonly network = inject(NetworkService);
  readonly install = inject(InstallService);

  readonly loading = signal(false);
  readonly message = signal<string | null>(null);
  readonly error = signal<string | null>(null);
  readonly offlineNotice = signal<string | null>(null);
  readonly showLogout = signal(false);
  readonly user = this.auth.user;
  readonly canWrite = computed(() => this.network.online() && !this.auth.isSessionExpired());

  readonly profileForm = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    telefono: [''],
  });

  readonly passwordForm = this.fb.nonNullable.group({
    password_actual: ['', [Validators.required]],
    password_nueva: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngOnInit(): void {
    this.patchProfileIfAvailable();
    this.loadProfile();
  }

  loadProfile(): void {
    if (!this.network.online()) {
      this.offlineNotice.set(
        'Sin conexion. Se muestran los datos guardados en este dispositivo; las escrituras estan deshabilitadas.',
      );
      this.patchProfileIfAvailable();
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.offlineNotice.set(null);
    this.auth.me().subscribe({
      next: (user) => this.patchProfile(user),
      error: (error) => {
        if (isNetworkError(error)) {
          this.offlineNotice.set(
            'No se pudo contactar al servidor. Se muestran los datos guardados en este dispositivo.',
          );
          this.patchProfileIfAvailable();
        } else {
          this.error.set(apiErrorMessage(error, 'No se pudo cargar el perfil.'));
        }
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }

  saveProfile(): void {
    if (this.profileForm.invalid) {
      this.profileForm.markAllAsTouched();
      return;
    }

    if (!this.canWrite()) {
      this.error.set('No puede guardar cambios sin conexion o con la sesion expirada.');
      return;
    }

    const raw = this.profileForm.getRawValue();
    this.loading.set(true);
    this.message.set(null);
    this.error.set(null);
    this.auth
      .updateMe({
        nombre: raw.nombre,
        telefono: raw.telefono.trim() ? raw.telefono.trim() : null,
      })
      .subscribe({
        next: () => this.message.set('Perfil actualizado correctamente.'),
        error: (error) => {
          if (isNetworkError(error)) {
            this.offlineNotice.set('Sin conexion. No se guardaron los cambios.');
          } else {
            this.error.set(apiErrorMessage(error, 'No se pudo actualizar el perfil.'));
          }
          this.loading.set(false);
        },
        complete: () => this.loading.set(false),
      });
  }

  changePassword(): void {
    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      return;
    }

    if (!this.canWrite()) {
      this.error.set('No puede cambiar la contrasena sin conexion o con la sesion expirada.');
      return;
    }

    this.loading.set(true);
    this.message.set(null);
    this.error.set(null);
    this.auth.changePassword(this.passwordForm.getRawValue()).subscribe({
      next: (response) => {
        this.message.set(response.mensaje);
        this.passwordForm.reset();
      },
      error: (error) => {
        if (isNetworkError(error)) {
          this.offlineNotice.set('Sin conexion. No se cambio la contrasena.');
        } else {
          this.error.set(apiErrorMessage(error, 'No se pudo cambiar la contrasena.'));
        }
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }

  requestLogout(): void {
    this.showLogout.set(true);
  }

  confirmLogout(): void {
    this.showLogout.set(false);
    this.auth.logout().subscribe();
  }

  async installApp(): Promise<void> {
    const accepted = await this.install.prompt();
    if (accepted) {
      this.message.set('FashionStore se esta instalando en este dispositivo.');
    }
  }

  private patchProfileIfAvailable(): void {
    const user = this.auth.user();
    if (user) {
      this.patchProfile(user);
    }
  }

  private patchProfile(user: User): void {
    this.profileForm.patchValue({
      nombre: user.nombre,
      telefono: user.telefono ?? '',
    });
  }
}
