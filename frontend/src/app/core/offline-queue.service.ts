import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private readonly queueKey = 'fashionstore_offline_queue';
  private readonly outboxKey = 'cola_operaciones_offline';

  readonly pendingSignal = signal<boolean>(this.hasPending());

  hasPending(): boolean {
    if (typeof localStorage === 'undefined') {
      return false;
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
          return outbox.some((o) => o && o.estado !== 'confirmada');
        }
      } catch {
        return true;
      }
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
