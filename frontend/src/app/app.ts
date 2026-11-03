import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { SwUpdate } from '@angular/service-worker';

import { AuthService } from './core/auth.service';
import { LogoutDialogComponent } from './core/logout-dialog.component';
import { NetworkService } from './core/network.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, LogoutDialogComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  readonly auth = inject(AuthService);
  readonly network = inject(NetworkService);
  readonly showLogout = signal(false);
  readonly updateReady = signal(false);

  private readonly swUpdate = inject(SwUpdate, { optional: true });

  constructor() {
    if (this.swUpdate?.isEnabled) {
      this.swUpdate.versionUpdates.subscribe((event) => {
        if (event.type === 'VERSION_READY') {
          this.updateReady.set(true);
        }
      });
    }
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
