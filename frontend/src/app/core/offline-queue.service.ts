import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private readonly queueKey = 'fashionstore_offline_queue';

  hasPending(): boolean {
    const raw = localStorage.getItem(this.queueKey);
    if (!raw) {
      return false;
    }
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.length > 0 : true;
    } catch {
      return true;
    }
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
  }

  clear(): void {
    localStorage.removeItem(this.queueKey);
  }
}
