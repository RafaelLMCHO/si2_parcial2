import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class NetworkService {
  readonly online = signal(typeof navigator === 'undefined' ? true : navigator.onLine);

  constructor() {
    if (typeof window === 'undefined') {
      return;
    }

    window.addEventListener('online', () => this.markOnline());
    window.addEventListener('offline', () => this.markOffline());
  }

  markOnline(): void {
    this.online.set(true);
  }

  markOffline(): void {
    this.online.set(false);
  }
}
