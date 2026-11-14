import { Injectable, inject, signal } from '@angular/core';
import { VentasOfflineStore } from './ventas-offline-store.service';

@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private readonly ventasStore = inject(VentasOfflineStore);
  private readonly queueKey = 'fashionstore_offline_queue';
  private readonly outboxKey = 'cola_operaciones_offline';

  readonly pendingSignal = signal<boolean>(this.hasPending());

  hasPending(): boolean {
    if (typeof localStorage === 'undefined') {
      return this.ventasStore.hasPending();
    }

    const raw = localStorage.getItem(this.queueKey);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) ? parsed.length > 0 : true) {
          return true;
        }
      } catch {
        return true;
      }
    }

    const rawOutbox = localStorage.getItem(this.outboxKey);
    if (rawOutbox) {
      try {
        const outbox = JSON.parse(rawOutbox);
        if (Array.isArray(outbox)) {
          if (outbox.some((o) => o && o.estado !== 'confirmada')) {
            return true;
          }
        }
      } catch {
        return true;
      }
    }

    if (this.ventasStore.hasPending()) {
      return true;
    }

    return false;
  }

  refreshStatus(): void {
    this.pendingSignal.set(this.hasPending());
  }

  enqueue(operation: unknown): void {
    const raw = localStorage.getItem(this.queueKey);
    let queue: unknown[] = [];
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          queue = parsed;
        }
      } catch {
        queue = [];
      }
    }
    queue.push(operation);
    localStorage.setItem(this.queueKey, JSON.stringify(queue));
    this.refreshStatus();
  }

  clear(): void {
    localStorage.removeItem(this.queueKey);
    this.refreshStatus();
  }
}
