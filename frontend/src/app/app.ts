import { Component, computed, effect, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SwUpdate } from '@angular/service-worker';
import { CommonModule } from '@angular/common';
import { EMPTY, catchError } from 'rxjs';

import { CU25DescargarCatalogoOfflineController } from './controller/cu25_descargar_catalogo_offline_controller';
import { CU31SincronizarOperacionesController } from './controller/cu31_sincronizar_operaciones_controller';
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
  private readonly cu25Offline = inject(CU25DescargarCatalogoOfflineController);
  private readonly cu31Sync = inject(CU31SincronizarOperacionesController);
  private wasOnline = this.network.online();

  constructor() {
    if (this.swUpdate?.isEnabled) {
      this.swUpdate.versionUpdates.subscribe((event) => {
        if (event.type === 'VERSION_READY') {
          this.updateReady.set(true);
          void this.swUpdate?.activateUpdate().catch(() => undefined);
        }
      });

      this.swUpdate.unrecoverable.subscribe(() => {
        window.location.reload();
      });

      if (this.network.online()) {
        void this.swUpdate.checkForUpdate().catch(() => undefined);
      }

      if (typeof window !== 'undefined') {
        window.addEventListener('focus', () => {
          if (this.network.online()) {
            void this.swUpdate?.checkForUpdate().catch(() => undefined);
          }
        });
      }
    }

    // Cerrar sidebar móvil en navegación
    this.router.events.subscribe(() => {
      this.mobileSidebarOpen.set(false);
    });

    // Prefetch offline silencioso al autenticar y auto-sincronización al volver en línea
    effect(() => {
      const online = this.network.online();
      const isAuth = this.auth.isAuthenticated();
      const user = this.auth.user();
      const tieneEmpresa = Boolean(user?.empresa_id);

      if (online && this.swUpdate?.isEnabled) {
        void this.swUpdate.checkForUpdate().catch(() => undefined);
      }

      if (isAuth && tieneEmpresa && online) {
        this.cu25Offline.asegurarCatalogoOfflineCargado();
        if (!this.wasOnline || this.auth.pendingOffline()) {
          if (!this.cu31Sync.cargando()) {
            this.cu31Sync
              .sincronizarLote()
              .pipe(catchError(() => EMPTY))
              .subscribe();
          }
        }
      } else if (!isAuth) {
        this.cu25Offline.resetPrefetch();
      }
      this.wasOnline = online;
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

  async reload(): Promise<void> {
    if (this.swUpdate?.isEnabled) {
      try {
        await this.swUpdate.activateUpdate();
      } catch {
        // Ignorar si ya fue activada
      }
    }
    window.location.reload();
  }
}

