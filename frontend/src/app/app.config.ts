import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  isDevMode,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';

import { routes } from './app.routes';
import { authInterceptor } from './core/auth.interceptor';
import { OfflineQueueService } from './core/offline-queue.service';
import { VentasOfflineStore } from './core/ventas-offline-store.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAppInitializer(() => {
      const ventasStore = inject(VentasOfflineStore);
      const offlineQueue = inject(OfflineQueueService);
      return (async () => {
        try {
          if (typeof indexedDB !== 'undefined') {
            await ventasStore.hydrate();
          }
        } catch (e) {
          console.warn('[AppInitializer] hydrate error:', e);
        } finally {
          offlineQueue.refreshStatus();
        }
      })();
    }),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerImmediately',
    }),
  ],
};
