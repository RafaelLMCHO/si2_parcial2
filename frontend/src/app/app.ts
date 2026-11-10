import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SwUpdate } from '@angular/service-worker';
import { CommonModule } from '@angular/common';

import { AuthService } from './core/auth.service';
import { LogoutDialogComponent } from './core/logout-dialog.component';
import { NetworkService } from './core/network.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, LogoutDialogComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  readonly auth = inject(AuthService);
  readonly network = inject(NetworkService);
  readonly router = inject(Router);

  readonly showLogout = signal(false);
  readonly updateReady = signal(false);

  // Estados de navegación del Shell SaaS
  readonly sidebarCollapsed = signal(false);
  readonly mobileSidebarOpen = signal(false);

  // Determina si la vista actual es para staff/backoffice o tienda boutique
  readonly isBackoffice = computed(() => {
    const user = this.auth.user();
    if (!user) return false;
    return ['superadmin', 'administrador', 'cajero', 'encargado'].includes(user.rol);
  });

  private readonly swUpdate = inject(SwUpdate, { optional: true });

  constructor() {
    if (this.swUpdate?.isEnabled) {
      this.swUpdate.versionUpdates.subscribe((event) => {
        if (event.type === 'VERSION_READY') {
          this.updateReady.set(true);
        }
      });
    }

    // Cerrar sidebar móvil en navegación
    this.router.events.subscribe(() => {
      this.mobileSidebarOpen.set(false);
    });
  }

  toggleSidebar(): void {
    this.sidebarCollapsed.update((v) => !v);
  }

  toggleMobileSidebar(): void {
    this.mobileSidebarOpen.update((v) => !v);
  }

  closeMobileSidebar(): void {
    this.mobileSidebarOpen.set(false);
  }

  requestLogout(): void {
    this.showLogout.set(true);
  }

  confirmLogout(): void {
    this.showLogout.set(false);
    this.auth.logout().subscribe();
  }

  reload(): void {
    window.location.reload();
  }
}

