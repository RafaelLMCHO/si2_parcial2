import { Injectable, signal } from '@angular/core';

export const DB_NAME = 'FashionStoreVentasOfflineDB';
export const DB_VERSION = 1;
export const STORE = 'ventas_offline';
export const MARKER_KEY = 'fashionstore_ventas_idb_initialized';
export const FALLBACK_KEY = 'fashionstore_ventas_offline';

export interface VentaOfflineRecord {
  id: string; // uuid local (igual al usado en CU-28)
  tipo: 'venta_offline';
  sucursal_id: string;
  payload: Record<string, unknown>;
  creada_en: string;
  idempotency_key: string; // 'VENTA-OFF-' + uuid
  estado: 'pendiente' | 'enviada' | 'confirmada' | 'en_conflicto';
  intentos: number;
  ultimo_error?: string;
}

export interface ConflictoSyncItem {
  id: string;
  detalle?: string;
  causa?: string;
}

@Injectable({ providedIn: 'root' })
export class VentasOfflineStore {
  private readonly itemsSignal = signal<VentaOfflineRecord[]>([]);
  readonly items = this.itemsSignal.asReadonly();

  private persistChain: Promise<void> = Promise.resolve();
  private dbPromise: Promise<IDBDatabase> | null = null;
  private fallback = false;
  private hydrated = false;

  list(): VentaOfflineRecord[] {
    return [...this.itemsSignal()];
  }

  listPendientes(): VentaOfflineRecord[] {
    return this.itemsSignal().filter((v) => v.estado === 'pendiente' || v.estado === 'enviada');
  }

  hasPending(): boolean {
    return this.itemsSignal().some((v) => v.estado !== 'confirmada');
  }

  async hydrate(): Promise<void> {
    if (this.hydrated) {
      return;
    }
    try {
      if (typeof indexedDB === 'undefined') {
        this.fallback = true;
        this.loadFallbackStorage();
        this.hydrated = true;
        return;
      }

      const marker = typeof localStorage !== 'undefined' ? localStorage.getItem(MARKER_KEY) : null;
      if (!marker) {
        // No existe marcador: verificar si hay ventas legacy en localStorage['cola_operaciones_offline']
        const legacyVentas = this.extractLegacyVentas();
        if (legacyVentas.length === 0) {
          // Lazy: no se abre la DB aún
          this.hydrated = true;
          return;
        }

        // Migrar ventas legacy a IndexedDB
        const db = await this.openDb();
        await this.migrarLegacyVentas(db, legacyVentas);
        this.itemsSignal.set(legacyVentas);
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(MARKER_KEY, '1');
        }
        this.hydrated = true;
        return;
      }

      // Existe marcador: leer todo el store de IndexedDB
      const db = await this.openDb();
      const records = await this.readAllFromDb(db);
      this.itemsSignal.set(records);
      this.hydrated = true;
    } catch (err) {
      console.warn('[VentasOfflineStore] Error durante hydrate():', err);
      // Fallback a almacenamiento en memoria / localStorage si falla IndexedDB
      this.fallback = true;
      this.loadFallbackStorage();
      this.hydrated = true;
    }
  }

  enqueue(record: VentaOfflineRecord): void {
    const next = [...this.itemsSignal(), record];
    this.itemsSignal.set(next);

    this.persistChain = this.persistChain
      .then(async () => {
        if (this.fallback) {
          this.saveFallbackStorage();
          return;
        }
        const db = await this.openDb();
        await this.putRecordInDb(db, record);
        if (typeof localStorage !== 'undefined' && !localStorage.getItem(MARKER_KEY)) {
          localStorage.setItem(MARKER_KEY, '1');
        }
        if (typeof navigator !== 'undefined' && navigator.storage?.persist) {
          navigator.storage.persist().catch(() => undefined);
        }
      })
      .catch((err) => {
        console.warn('[VentasOfflineStore] Fallo al persistir venta encolada:', err);
      });
  }

  markEnviadas(ids: string[]): void {
    if (!ids || ids.length === 0) return;
    const idSet = new Set(ids);
    const updatedRecords: VentaOfflineRecord[] = [];

    const next = this.itemsSignal().map((item) => {
      if (idSet.has(item.id)) {
        const updated: VentaOfflineRecord = { ...item, estado: 'enviada' };
        updatedRecords.push(updated);
        return updated;
      }
      return item;
    });
    this.itemsSignal.set(next);

    this.persistChain = this.persistChain
      .then(async () => {
        if (this.fallback) {
          this.saveFallbackStorage();
          return;
        }
        const db = await this.openDb();
        await this.putMultipleInDb(db, updatedRecords);
      })
      .catch((err) => {
        console.warn('[VentasOfflineStore] Fallo al marcar enviadas:', err);
      });
  }

  applySyncResult(confirmados: string[], conflictos: ConflictoSyncItem[]): void {
    const confSet = new Set(confirmados || []);
    const conflictMap = new Map<string, ConflictoSyncItem>();
    for (const c of conflictos || []) {
      conflictMap.set(c.id, c);
    }

    const updatedRecords: VentaOfflineRecord[] = [];
    const next = this.itemsSignal().map((item) => {
      if (confSet.has(item.id)) {
        const { ultimo_error, ...rest } = item;
        const updated: VentaOfflineRecord = { ...rest, estado: 'confirmada' };
        updatedRecords.push(updated);
        return updated;
      }
      const conf = conflictMap.get(item.id);
      if (conf) {
        const errDetail = conf.detalle || conf.causa || 'Conflicto de stock al sincronizar';
        const updated: VentaOfflineRecord = {
          ...item,
          estado: 'en_conflicto',
          ultimo_error: errDetail,
        };
        updatedRecords.push(updated);
        return updated;
      }
      return item;
    });
    this.itemsSignal.set(next);

    this.persistChain = this.persistChain
      .then(async () => {
        if (this.fallback) {
          this.saveFallbackStorage();
          return;
        }
        const db = await this.openDb();
        await this.putMultipleInDb(db, updatedRecords);
      })
      .catch((err) => {
        console.warn('[VentasOfflineStore] Fallo al aplicar resultado de sync:', err);
      });
  }

  revertEnviadas(): void {
    const updatedRecords: VentaOfflineRecord[] = [];
    const next = this.itemsSignal().map((item) => {
      if (item.estado === 'enviada') {
        const updated: VentaOfflineRecord = { ...item, estado: 'pendiente' };
        updatedRecords.push(updated);
        return updated;
      }
      return item;
    });
    this.itemsSignal.set(next);

    this.persistChain = this.persistChain
      .then(async () => {
        if (this.fallback) {
          this.saveFallbackStorage();
          return;
        }
        const db = await this.openDb();
        await this.putMultipleInDb(db, updatedRecords);
      })
      .catch((err) => {
        console.warn('[VentasOfflineStore] Fallo al revertir enviadas:', err);
      });
  }

  remove(id: string): void {
    const next = this.itemsSignal().filter((v) => v.id !== id);
    this.itemsSignal.set(next);

    this.persistChain = this.persistChain
      .then(async () => {
        if (this.fallback) {
          this.saveFallbackStorage();
          return;
        }
        const db = await this.openDb();
        await this.deleteFromDb(db, id);
      })
      .catch((err) => {
        console.warn('[VentasOfflineStore] Fallo al eliminar venta:', err);
      });
  }

  whenIdle(): Promise<void> {
    return this.persistChain;
  }

  async close(): Promise<void> {
    if (this.dbPromise) {
      const p = this.dbPromise;
      this.dbPromise = null;
      try {
        const db = await p;
        db.close();
      } catch {
        // noop
      }
    }
  }

  private openDb(): Promise<IDBDatabase> {
    if (this.dbPromise) {
      return this.dbPromise;
    }

    this.dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE)) {
          const store = db.createObjectStore(STORE, { keyPath: 'id' });
          store.createIndex('estado', 'estado', { unique: false });
        }
      };

      request.onsuccess = () => {
        const db = request.result;
        db.onversionchange = () => {
          db.close();
          this.dbPromise = null;
        };
        db.onclose = () => {
          this.dbPromise = null;
        };
        resolve(db);
      };

      request.onerror = () => {
        this.dbPromise = null;
        reject(request.error || new Error('No se pudo abrir IndexedDB'));
      };
    });

    return this.dbPromise;
  }

  private readAllFromDb(db: IDBDatabase): Promise<VentaOfflineRecord[]> {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const store = tx.objectStore(STORE);
      const req = store.getAll();
      req.onsuccess = () => resolve((req.result as VentaOfflineRecord[]) || []);
      req.onerror = () => reject(req.error || new Error('Error al leer IndexedDB'));
    });
  }

  private putRecordInDb(db: IDBDatabase, record: VentaOfflineRecord): Promise<void> {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      store.put(record);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Error al guardar en IndexedDB'));
      tx.onabort = () => reject(tx.error || new Error('Transacción abortada en IndexedDB'));
    });
  }

  private putMultipleInDb(db: IDBDatabase, records: VentaOfflineRecord[]): Promise<void> {
    if (records.length === 0) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      for (const rec of records) {
        store.put(rec);
      }
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Error al guardar múltiples en IndexedDB'));
      tx.onabort = () => reject(tx.error || new Error('Transacción abortada en IndexedDB'));
    });
  }

  private deleteFromDb(db: IDBDatabase, id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      store.delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Error al eliminar en IndexedDB'));
      tx.onabort = () => reject(tx.error || new Error('Transacción abortada en IndexedDB'));
    });
  }

  private extractLegacyVentas(): VentaOfflineRecord[] {
    if (typeof localStorage === 'undefined') return [];
    try {
      const raw = localStorage.getItem('cola_operaciones_offline');
      if (!raw) return [];
      const parsed: any[] = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];

      const map = new Map<string, VentaOfflineRecord>();
      for (const item of parsed) {
        if (item && item.tipo === 'venta_offline' && item.id) {
          const rec: VentaOfflineRecord = {
            id: String(item.id),
            tipo: 'venta_offline',
            sucursal_id: String(item.sucursal_id || item.payload?.sucursal_id || ''),
            payload: item.payload || {},
            creada_en: String(item.creada_en || item.payload?.fecha_hora_local || new Date().toISOString()),
            idempotency_key: String(item.idempotency_key || 'VENTA-OFF-' + item.id),
            estado: (['pendiente', 'enviada', 'confirmada', 'en_conflicto'].includes(item.estado)
              ? item.estado
              : 'pendiente') as VentaOfflineRecord['estado'],
            intentos: Number(item.intentos || 0),
            ultimo_error: item.ultimo_error,
          };
          // Dedupe por id (conservar el último)
          map.set(rec.id, rec);
        }
      }
      return Array.from(map.values());
    } catch {
      return [];
    }
  }

  private async migrarLegacyVentas(db: IDBDatabase, ventas: VentaOfflineRecord[]): Promise<void> {
    // 1. Guardar en IndexedDB
    await this.putMultipleInDb(db, ventas);

    // 2. Reescribir localStorage['cola_operaciones_offline'] conservando SOLO las no-ventas
    if (typeof localStorage !== 'undefined') {
      try {
        const raw = localStorage.getItem('cola_operaciones_offline');
        if (raw) {
          const parsed: any[] = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            const noVentas = parsed.filter((item) => item && item.tipo !== 'venta_offline');
            localStorage.setItem('cola_operaciones_offline', JSON.stringify(noVentas));
          }
        }
      } catch (err) {
        console.warn('[VentasOfflineStore] Error al reescribir cola legacy en localStorage:', err);
      }
    }
  }

  private loadFallbackStorage(): void {
    if (typeof localStorage === 'undefined') return;
    try {
      const raw = localStorage.getItem(FALLBACK_KEY);
      if (raw) {
        const parsed: VentaOfflineRecord[] = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          this.itemsSignal.set(parsed);
          return;
        }
      }
    } catch {
      // Ignorar fallback corrupto
    }
    this.itemsSignal.set([]);
  }

  private saveFallbackStorage(): void {
    if (typeof localStorage === 'undefined') return;
    try {
      localStorage.setItem(FALLBACK_KEY, JSON.stringify(this.itemsSignal()));
    } catch (err) {
      console.warn('[VentasOfflineStore] Error al guardar fallback en localStorage:', err);
    }
  }
}

