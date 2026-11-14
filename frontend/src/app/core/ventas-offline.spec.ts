import 'fake-indexeddb/auto';

import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { CU28VentaContadoOfflineController } from '../controller/cu28_venta_contado_offline_controller';
import { CU31SincronizarOperacionesController } from '../controller/cu31_sincronizar_operaciones_controller';
import { OfflineQueueService } from './offline-queue.service';
import {
  DB_NAME,
  DB_VERSION,
  FALLBACK_KEY,
  MARKER_KEY,
  STORE,
  VentaOfflineRecord,
  VentasOfflineStore,
} from './ventas-offline-store.service';

function deleteDb(): Promise<void> {
  return new Promise((resolve) => {
    const req = indexedDB.deleteDatabase(DB_NAME);
    req.onsuccess = () => resolve();
    req.onerror = () => resolve();
    req.onblocked = () => resolve();
  });
}

describe('Ventas Offline Web IndexedDB (CU-28 / CU-31)', () => {
  let httpMock: HttpTestingController;
  let store: VentasOfflineStore;
  let offlineQueue: OfflineQueueService;

  beforeEach(async () => {
    localStorage.clear();
    if (store) {
      await store.close();
    }
    await deleteDb();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    httpMock = TestBed.inject(HttpTestingController);
    store = TestBed.inject(VentasOfflineStore);
    offlineQueue = TestBed.inject(OfflineQueueService);
  });

  afterEach(async () => {
    httpMock.verify();
    if (store) {
      await store.close();
    }
    localStorage.clear();
    await deleteDb();
  });

  it('[T1] Sin ventas ni marcador, hydrate() no abre la DB', async () => {
    const openSpy = spyOn(indexedDB, 'open').and.callThrough();
    await store.hydrate();
    expect(openSpy).not.toHaveBeenCalled();
    expect(store.list().length).toBe(0);
    expect(store.hasPending()).toBeFalse();
  });

  it('[T2] registrarVenta() encola en el espejo, persiste en IDB y hasPending() pasa a true', async () => {
    await store.hydrate();
    expect(offlineQueue.hasPending()).toBeFalse();

    const ventaCtrl = TestBed.inject(CU28VentaContadoOfflineController);
    const ticket = ventaCtrl.registrarVenta({
      sucursal_id: 'suc-1',
      usuario_id: 'usr-1',
      cliente_nombre: 'Cliente Test',
      cliente_documento: '12345',
      lineas: [{ variante_id: 'var-1', sku: 'SKU-1', cantidad: 2, precio_unitario: 50 }],
      total: 100,
      metodo_pago: 'efectivo',
    });

    expect(ticket).toBeTruthy();
    expect(ticket.uuid).toBeTruthy();
    expect(store.list().length).toBe(1);
    expect(store.hasPending()).toBeTrue();
    expect(offlineQueue.hasPending()).toBeTrue();

    await store.whenIdle();

    // Verificar directamente en IndexedDB
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    const db: IDBDatabase = await new Promise((res) => {
      req.onsuccess = () => res(req.result);
    });
    const tx = db.transaction(STORE, 'readonly');
    const all: VentaOfflineRecord[] = await new Promise((res) => {
      const getReq = tx.objectStore(STORE).getAll();
      getReq.onsuccess = () => res(getReq.result);
    });
    db.close();

    expect(all.length).toBe(1);
    expect(all[0].id).toBe(ticket.uuid);
    expect(all[0].estado).toBe('pendiente');
    expect(all[0].tipo).toBe('venta_offline');
  });

  it('[T3] Persistencia sobrevive a nueva instancia tras enqueue y hydrate', async () => {
    await store.hydrate();
    const ventaCtrl = TestBed.inject(CU28VentaContadoOfflineController);
    ventaCtrl.registrarVenta({
      sucursal_id: 'suc-1',
      usuario_id: 'usr-1',
      cliente_nombre: 'Cliente Test',
      cliente_documento: '12345',
      lineas: [{ variante_id: 'var-1', sku: 'SKU-1', cantidad: 1, precio_unitario: 100 }],
      total: 100,
      metodo_pago: 'efectivo',
    });
    await store.whenIdle();
    await store.close();

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    const newStore = TestBed.inject(VentasOfflineStore);
    await newStore.hydrate();

    expect(newStore.list().length).toBe(1);
    expect(newStore.list()[0].sucursal_id).toBe('suc-1');
    expect(newStore.hasPending()).toBeTrue();
    await newStore.close();
  });

  it('[T4] Migracion legacy extrae ventas a IDB, conserva reservas en localStorage y crea MARKER_KEY', async () => {
    const legacyQueue = [
      {
        id: 'legacy-venta-1',
        tipo: 'venta_offline',
        sucursal_id: 'suc-1',
        payload: { total: 150 },
        creada_en: '2026-11-10T10:00:00.000Z',
        idempotency_key: 'VENTA-OFF-legacy-venta-1',
        estado: 'pendiente',
      },
      {
        id: 'legacy-reserva-1',
        tipo: 'reserva_offline',
        sucursal_id: 'suc-1',
        payload: { items: [] },
        creada_en: '2026-11-10T10:05:00.000Z',
        idempotency_key: 'IDEMP-legacy-reserva-1',
        estado: 'pendiente',
      },
      {
        // duplicado intencional para verificar deduplicación por id
        id: 'legacy-venta-1',
        tipo: 'venta_offline',
        sucursal_id: 'suc-1',
        payload: { total: 200 },
        creada_en: '2026-11-10T10:10:00.000Z',
        idempotency_key: 'VENTA-OFF-legacy-venta-1',
        estado: 'pendiente',
      },
    ];
    localStorage.setItem('cola_operaciones_offline', JSON.stringify(legacyQueue));
    expect(localStorage.getItem(MARKER_KEY)).toBeNull();

    await store.hydrate();

    // Venta en IDB deduplicada
    expect(store.list().length).toBe(1);
    expect(store.list()[0].id).toBe('legacy-venta-1');
    expect(store.list()[0].payload['total']).toBe(200);

    // localStorage conserva solo la reserva
    const postCola = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
    expect(postCola.length).toBe(1);
    expect(postCola[0].tipo).toBe('reserva_offline');
    expect(postCola[0].id).toBe('legacy-reserva-1');

    // Marcador establecido
    expect(localStorage.getItem(MARKER_KEY)).toBe('1');
  });

  it('[T5] CU-31 arma lote combinado (IDB + localStorage), sincroniza y actualiza confirmadas', (done) => {
    // 1. Preparar reserva en localStorage
    const reservaItem = {
      id: 'reserva-sync-1',
      tipo: 'reserva_offline',
      sucursal_id: 'suc-1',
      payload: { test: true },
      creada_en: '2026-11-14T12:00:00.000Z',
      idempotency_key: 'IDEMP-reserva-sync-1',
      estado: 'pendiente',
    };
    localStorage.setItem('cola_operaciones_offline', JSON.stringify([reservaItem]));

    // 2. Encolar venta en VentasOfflineStore
    store.enqueue({
      id: 'venta-sync-1',
      tipo: 'venta_offline',
      sucursal_id: 'suc-1',
      payload: { total: 100 },
      creada_en: '2026-11-14T12:01:00.000Z',
      idempotency_key: 'VENTA-OFF-venta-sync-1',
      estado: 'pendiente',
      intentos: 0,
    });

    expect(offlineQueue.hasPending()).toBeTrue();

    const cu31 = TestBed.inject(CU31SincronizarOperacionesController);
    cu31.sincronizarLote().subscribe({
      next: (res) => {
        expect(res.confirmados).toContain('reserva-sync-1');
        expect(res.confirmados).toContain('venta-sync-1');

        // Comprobar que en el store de ventas está confirmada
        const vRec = store.list().find((x) => x.id === 'venta-sync-1');
        expect(vRec?.estado).toBe('confirmada');

        // Comprobar que en localStorage la reserva está confirmada
        const cola = JSON.parse(localStorage.getItem('cola_operaciones_offline') || '[]');
        const rRec = cola.find((x: any) => x.id === 'reserva-sync-1');
        expect(rRec?.estado).toBe('confirmada');

        // hasPending() debe ser false
        expect(store.hasPending()).toBeFalse();
        expect(offlineQueue.hasPending()).toBeFalse();
        store.whenIdle().then(() => store.close()).finally(done);
      },
    });

    const req = httpMock.expectOne('/api/v1/sync');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.operaciones.length).toBe(2);
    expect(req.request.body.operaciones.map((o: any) => o.id)).toEqual(['reserva-sync-1', 'venta-sync-1']);

    req.flush({
      procesados_total: 2,
      confirmados: ['reserva-sync-1', 'venta-sync-1'],
      conflictos: [],
    });
  });

  it('[T6] Fallback cuando indexedDB no está disponible usa FALLBACK_KEY en localStorage', async () => {
    const originalIdb = window.indexedDB;
    try {
      // @ts-expect-error simular entorno sin indexedDB
      delete window.indexedDB;

      TestBed.resetTestingModule();
      TestBed.configureTestingModule({
        providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
      });
      const fallbackStore = TestBed.inject(VentasOfflineStore);
      await fallbackStore.hydrate();

      const record: VentaOfflineRecord = {
        id: 'fallback-venta-1',
        tipo: 'venta_offline',
        sucursal_id: 'suc-fallback',
        payload: { total: 350 },
        creada_en: new Date().toISOString(),
        idempotency_key: 'VENTA-OFF-fallback-venta-1',
        estado: 'pendiente',
        intentos: 0,
      };

      fallbackStore.enqueue(record);
      await fallbackStore.whenIdle();

      expect(fallbackStore.list().length).toBe(1);
      expect(fallbackStore.hasPending()).toBeTrue();

      const raw = localStorage.getItem(FALLBACK_KEY);
      expect(raw).toBeTruthy();
      const parsed = JSON.parse(raw!);
      expect(parsed.length).toBe(1);
      expect(parsed[0].id).toBe('fallback-venta-1');
    } finally {
      window.indexedDB = originalIdb;
    }
  });
});

