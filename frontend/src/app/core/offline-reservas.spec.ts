import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { CU25DescargarCatalogoOfflineController } from '../controller/cu25_descargar_catalogo_offline_controller';
import {
  CU26RegistrarReservaOfflineController,
  generarUuidV4,
} from '../controller/cu26_registrar_reserva_offline_controller';
import { CU31SincronizarOperacionesController } from '../controller/cu31_sincronizar_operaciones_controller';
import { CatalogoService } from './catalogo.service';
import { InventarioService } from './inventario.service';
import { NetworkService } from './network.service';
import { OfflineQueueService } from './offline-queue.service';
import { ReservaService } from './reserva.service';

describe('Offline Reservas Web (CU-25 / CU-26 / CU-31)', () => {
  let httpMock: HttpTestingController;
  let network: NetworkService;
  let offlineQueue: OfflineQueueService;
  let cu25: CU25DescargarCatalogoOfflineController;
  let cu26: CU26RegistrarReservaOfflineController;
  let cu31: CU31SincronizarOperacionesController;
  let catalogo: CatalogoService;
  let inventario: InventarioService;
  let reservas: ReservaService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    httpMock = TestBed.inject(HttpTestingController);
    network = TestBed.inject(NetworkService);
    offlineQueue = TestBed.inject(OfflineQueueService);
    cu25 = TestBed.inject(CU25DescargarCatalogoOfflineController);
    cu26 = TestBed.inject(CU26RegistrarReservaOfflineController);
    cu31 = TestBed.inject(CU31SincronizarOperacionesController);
    catalogo = TestBed.inject(CatalogoService);
    inventario = TestBed.inject(InventarioService);
    reservas = TestBed.inject(ReservaService);
    network.markOnline();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('generarUuidV4 y CU-26 encolan reserva con UUID RFC-4122 valido y actualizan OfflineQueueService', () => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
    const sampleId = generarUuidV4();
    expect(uuidRegex.test(sampleId)).toBeTrue();

    expect(offlineQueue.hasPending()).toBeFalse();
    expect(offlineQueue.pendingSignal()).toBeFalse();

    const id = cu26.registrarReserva({
      sucursal_id: 'suc-matriz-1',
      sucursal_nombre: 'Casa Matriz',
      fecha_visita: new Date(Date.now() + 86400000).toISOString(),
      probador: true,
      items: [{ variante_id: 'var-1', cantidad: 1, prenda_nombre: 'Vestido midi' }],
    });

    expect(uuidRegex.test(id)).toBeTrue();
    expect(offlineQueue.hasPending()).toBeTrue();
    expect(offlineQueue.pendingSignal()).toBeTrue();
    expect(cu26.listarPendientes().length).toBe(1);
    expect(cu26.esReservaLocal(id)).toBeTrue();

    expect(cu26.cancelarReservaLocal(id)).toBeTrue();
    expect(offlineQueue.hasPending()).toBeFalse();
    expect(offlineQueue.pendingSignal()).toBeFalse();
  });

  it('CU-25 cachea sucursales y CatalogoService/InventarioService las resuelven offline con descuento de soft-locks', async () => {
    const pkg = {
      empresa_id: 'emp-demo',
      generado_en: '2026-11-11T10:00:00Z',
      total_articulos: 1,
      sucursales: [
        {
          id: 'suc-1',
          nombre: 'Casa Matriz',
          direccion: 'Av Central 100',
          ciudad: 'Santa Cruz',
          es_matriz: true,
        },
        {
          id: 'suc-2',
          nombre: 'Sucursal Norte',
          direccion: 'Av Banzer 4to Anillo',
          ciudad: 'Santa Cruz',
          es_matriz: false,
        },
      ],
      prendas: [
        {
          id: 'prenda-1',
          codigo: 'FS-001',
          nombre: 'Vestido midi',
          genero: 'mujer',
          precio_base: 180,
          categoria_id: 'cat-1',
        },
      ],
      variantes: [
        {
          id: 'var-1',
          prenda_id: 'prenda-1',
          sku: 'FS-001-M-AZ',
          precio_venta: 180,
          talla: 'M',
          color: 'Azul',
        },
      ],
      existencias: [
        { variante_id: 'var-1', sucursal_id: 'suc-1', stock_disponible: 5 },
        { variante_id: 'var-1', sucursal_id: 'suc-2', stock_disponible: 2 },
      ],
    };

    const dlPromise = firstValueFrom(cu25.descargarCatalogo());
    const req = httpMock.expectOne('/api/v1/sync/catalogo-offline');
    expect(req.request.method).toBe('GET');
    req.flush(pkg);
    await dlPromise;

    expect(cu25.sucursalesDescargadas()).toBe(2);
    expect(cu25.obtenerSucursalesCacheadas().length).toBe(2);

    // Simular soft-lock activo de 2 unidades en Casa Matriz
    localStorage.setItem(
      'soft_locks_locales',
      JSON.stringify([
        {
          id: 'lock-1',
          variante_id: 'var-1',
          sucursal_id: 'suc-1',
          cantidad: 2,
          expira_en: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
        },
      ]),
    );

    network.markOffline();

    const prendaOffline = await firstValueFrom(catalogo.obtenerPrendaPorId('prenda-1'));
    expect(prendaOffline.nombre).toBe('Vestido midi');
    expect(prendaOffline.variantes.length).toBe(1);

    const disp = await firstValueFrom(inventario.consultarDisponibilidad('prenda-1'));
    expect(disp.es_local).toBeTrue();
    expect(disp.sucursales.length).toBe(2);
    const matriz = disp.sucursales.find((s) => s.sucursal_id === 'suc-1');
    expect(matriz?.variantes[0].stock_disponible).toBe(3);
  });

  it('ReservaService encola offline al perder red, lista pendientes, cancela local y sincroniza con CU-31', async () => {
    const fechaVisita = new Date(Date.now() + 86400000).toISOString();
    network.markOffline();

    const resOffline = await firstValueFrom(
      reservas.crearReserva({
        sucursal_id: 'suc-1',
        sucursal_nombre: 'Casa Matriz',
        fecha_visita: fechaVisita,
        probador: true,
        items: [
          {
            variante_id: 'var-1',
            cantidad: 1,
            prenda_nombre: 'Vestido midi',
            talla: 'M',
            color: 'Azul',
            sku: 'FS-001-M-AZ',
          },
        ],
      }),
    );

    expect(resOffline.offline).toBeTrue();
    expect(resOffline.estado).toBe('pendiente_sync');
    expect(resOffline.codigo).toMatch(/^RES-OFF-/);
    expect(offlineQueue.pendingSignal()).toBeTrue();

    const misOffline = await firstValueFrom(reservas.obtenerMisReservas());
    expect(misOffline.items.length).toBe(1);
    expect(misOffline.items[0].id).toBe(resOffline.id);
    expect(misOffline.items[0].sucursal_nombre).toBe('Casa Matriz');

    // Al volver a estar en linea, CU-31 sincroniza el lote con el backend y marca confirmada
    network.markOnline();
    const syncPromise = firstValueFrom(cu31.sincronizarLote());
    const syncReq = httpMock.expectOne('/api/v1/sync');
    expect(syncReq.request.method).toBe('POST');
    expect(syncReq.request.body.operaciones.length).toBe(1);
    expect(syncReq.request.body.operaciones[0].id).toBe(resOffline.id);
    expect(syncReq.request.body.operaciones[0].tipo).toBe('reserva_offline');
    expect(syncReq.request.body.operaciones[0].sucursal_id).toBe('suc-1');

    syncReq.flush({
      procesados_total: 1,
      confirmados: [resOffline.id],
      conflictos: [],
    });
    await syncPromise;

    expect(cu31.confirmados()).toBe(1);
    expect(cu31.conflictos()).toBe(0);
    expect(offlineQueue.hasPending()).toBeFalse();
    expect(offlineQueue.pendingSignal()).toBeFalse();
  });

  it('ReservaService encola cuando falla la red en vuelo (HTTP 0) y envia payload limpio cuando hay red', async () => {
    const fechaVisita = new Date(Date.now() + 86400000).toISOString();

    // Caso 1: Online pero HTTP status 0 -> fallback offline
    const fallbackPromise = firstValueFrom(
      reservas.crearReserva({
        sucursal_id: 'suc-1',
        sucursal_nombre: 'Casa Matriz',
        fecha_visita: fechaVisita,
        items: [{ variante_id: 'var-1', cantidad: 2, prenda_nombre: 'Camisa' }],
      }),
    );
    const failedReq = httpMock.expectOne('/api/v1/reservas');
    failedReq.error(new ProgressEvent('error'), { status: 0, statusText: 'Unknown Error' });
    const fallbackRes = await fallbackPromise;
    expect(fallbackRes.offline).toBeTrue();
    expect(fallbackRes.estado).toBe('pendiente_sync');

    // Cancelar reserva offline local limpia la cola
    const cancelRes = await firstValueFrom(reservas.cancelarReserva(fallbackRes.id));
    expect(cancelRes.estado).toBe('cancelada');
    expect(offlineQueue.hasPending()).toBeFalse();

    // Caso 2: Online OK -> envia contrato estricto sin campos extra
    const okPromise = firstValueFrom(
      reservas.crearReserva(
        {
          sucursal_id: 'suc-1',
          sucursal_nombre: 'Casa Matriz',
          fecha_visita: fechaVisita,
          probador: true,
          items: [{ variante_id: 'var-1', cantidad: 1, prenda_nombre: 'Camisa' }],
        },
        'idemp-fixed-123',
      ),
    );
    const okReq = httpMock.expectOne('/api/v1/reservas');
    expect(okReq.request.headers.get('Idempotency-Key')).toBe('idemp-fixed-123');
    expect(okReq.request.body).toEqual({
      sucursal_id: 'suc-1',
      fecha_visita: fechaVisita,
      items: [{ variante_id: 'var-1', cantidad: 1 }],
    });
    okReq.flush({
      id: 'srv-1',
      empresa_id: 'emp-1',
      usuario_id: 'u-1',
      sucursal_id: 'suc-1',
      codigo: 'RSV-0001',
      estado: 'pendiente_preparacion',
      fecha_visita: fechaVisita,
      expira_en: fechaVisita,
      items: [],
      created_at: fechaVisita,
    });
    const okRes = await okPromise;
    expect(okRes.codigo).toBe('RSV-0001');
  });
});

