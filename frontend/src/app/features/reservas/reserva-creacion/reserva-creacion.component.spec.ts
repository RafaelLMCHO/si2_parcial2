import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { CU25DescargarCatalogoOfflineController } from '../../../controller/cu25_descargar_catalogo_offline_controller';
import { AuthService } from '../../../core/auth.service';
import { CatalogoService } from '../../../core/catalogo.service';
import { InventarioService } from '../../../core/inventario.service';
import { NetworkService } from '../../../core/network.service';
import { SessionStoreService } from '../../../core/session-store.service';
import {
  ReservaCreacionComponent,
  extraerMensajeErrorReserva,
} from './reserva-creacion.component';

describe('ReservaCreacionComponent & aislamiento multi-tenant', () => {
  let httpMock: HttpTestingController;
  let network: NetworkService;
  let store: SessionStoreService;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [ReservaCreacionComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    network = TestBed.inject(NetworkService);
    store = TestBed.inject(SessionStoreService);
    network.markOnline();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('extraerMensajeErrorReserva traduce errores Pydantic 422 de UUID a mensajes claros sin [object Object]', () => {
    const errSucursal = {
      status: 422,
      error: {
        detail: [
          {
            type: 'uuid_parsing',
            loc: ['body', 'sucursal_id'],
            msg: 'Input should be a valid UUID',
            input: 'Sucursal Centro',
          },
        ],
      },
    };
    const msgSuc = extraerMensajeErrorReserva(errSucursal);
    expect(msgSuc).toContain('sucursal');
    expect(msgSuc).not.toContain('object Object');

    const errVariante = {
      status: 422,
      error: {
        detail: [
          {
            type: 'uuid_parsing',
            loc: ['body', 'items', 0, 'variante_id'],
            msg: 'Input should be a valid UUID',
          },
        ],
      },
    };
    expect(extraerMensajeErrorReserva(errVariante)).toContain('variante');

    expect(
      extraerMensajeErrorReserva({
        status: 422,
        error: { detail: { message: 'Stock insuficiente en Sucursal Centro' } },
      }),
    ).toBe('Stock insuficiente en Sucursal Centro');

    expect(extraerMensajeErrorReserva({ status: 401 })).toContain('sesión ha expirado');
  });

  it('muestra selectores para cliente, oculta tab CU-21 y valida UUID antes de enviar reserva', () => {
    store.saveSession({
      access_token: 'tok-cli',
      refresh_token: 'ref-cli',
      token_type: 'bearer',
      expires_in: 3600,
      usuario: {
        id: 'u-cli-1',
        empresa_id: '11111111-1111-1111-1111-111111111100',
        rol: 'cliente',
        nombre: 'Ana Cliente',
        correo: 'cliente@demo.com',
        email_verificado: true,
        estado: 'activo',
      },
    });

    const fixture = TestBed.createComponent(ReservaCreacionComponent);
    const comp = fixture.componentInstance;
    fixture.detectChanges();

    expect(comp.esStaff()).toBeFalse();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).not.toContain('CU-21: Preparación Staff Tienda');

    // Responder carga de catalogo offline CU-25 + catalogo online
    const syncReq = httpMock.expectOne('/api/v1/sync/catalogo-offline');
    syncReq.flush({
      empresa_id: '11111111-1111-1111-1111-111111111100',
      generado_en: new Date().toISOString(),
      total_articulos: 1,
      sucursales: [
        {
          id: '11111111-1111-1111-1111-111111111101',
          nombre: 'Sucursal Centro',
          direccion: 'Av. Central 10',
          ciudad: 'Santa Cruz',
          es_matriz: true,
        },
        {
          id: '11111111-1111-1111-1111-111111111102',
          nombre: 'Sucursal Norte',
          direccion: 'Av. Banzer 40',
          ciudad: 'Santa Cruz',
          es_matriz: false,
        },
      ],
      prendas: [],
      variantes: [],
      existencias: [],
    });

    const catReq = httpMock.expectOne('/api/v1/catalogo/prendas');
    catReq.flush({
      version_catalogo: 2,
      total: 1,
      items: [
        {
          id: '33333333-3333-3333-3333-333333333301',
          empresa_id: '11111111-1111-1111-1111-111111111100',
          codigo: 'FS-001',
          nombre: 'Vestido midi',
          genero: 'mujer',
          precio_base: 180,
          moneda: 'BOB',
          categoria_id: 'cat-1',
          estado: 'activa',
          created_at: '',
          updated_at: '',
          variantes: [
            {
              id: '22222222-2222-2222-2222-222222222201',
              prenda_id: '33333333-3333-3333-3333-333333333301',
              talla_id: 1,
              talla_nombre: 'XS',
              color_id: 1,
              color_nombre: 'Azul Marino',
              sku: 'FS-001-XS-AZ',
              precio_venta: 180,
              costo: 90,
              estado: 'activa',
              created_at: '',
              updated_at: '',
            },
          ],
        },
      ],
    });

    const dispReq = httpMock.expectOne(
      '/api/v1/inventario/prendas/33333333-3333-3333-3333-333333333301/disponibilidad',
    );
    dispReq.flush({
      prenda_id: '33333333-3333-3333-3333-333333333301',
      agotado_en_todas: false,
      actualizado_en: new Date().toISOString(),
      sucursales: [
        {
          sucursal_id: '11111111-1111-1111-1111-111111111101',
          nombre: 'Sucursal Centro',
          direccion: 'Av Central',
          ciudad: 'Santa Cruz',
          variantes: [
            {
              variante_id: '22222222-2222-2222-2222-222222222201',
              sku: 'FS-001-XS-AZ',
              talla: 'XS',
              color: 'Azul Marino',
              stock_disponible: 12,
            },
          ],
        },
      ],
    });

    fixture.detectChanges();
    expect(comp.sucursalesOpciones().length).toBe(2);
    expect(comp.varianteId()).toBe('22222222-2222-2222-2222-222222222201');
    expect(comp.sucursalId()).toBe('11111111-1111-1111-1111-111111111101');
    expect(compiled.querySelector('#res-prenda')).toBeTruthy();
    expect(compiled.querySelector('#res-variante')).toBeTruthy();
    expect(compiled.querySelector('#res-sucursal')).toBeTruthy();

    // Si se ingresa un texto no-UUID manualmente, bloquea antes de enviar POST
    comp.sucursalId.set('Sucursal Centro');
    comp.crear();
    expect(comp.esError()).toBeTrue();
    expect(comp.mensaje()).toContain('UUID válido');

    // Con UUID valido envia POST /api/v1/reservas y confirma exito
    comp.sucursalId.set('11111111-1111-1111-1111-111111111101');
    comp.crear();
    const postReq = httpMock.expectOne('/api/v1/reservas');
    expect(postReq.request.method).toBe('POST');
    expect(postReq.request.body.sucursal_id).toBe('11111111-1111-1111-1111-111111111101');
    postReq.flush({
      id: 'res-uuid-1',
      empresa_id: '11111111-1111-1111-1111-111111111100',
      usuario_id: 'u-cli-1',
      sucursal_id: '11111111-1111-1111-1111-111111111101',
      codigo: 'RSV-0099',
      estado: 'pendiente_preparacion',
      fecha_visita: new Date(Date.now() + 86400000).toISOString(),
      expira_en: new Date(Date.now() + 2 * 86400000).toISOString(),
      items: [],
      created_at: new Date().toISOString(),
    });
    expect(comp.esError()).toBeFalse();
    expect(comp.mensaje()).toContain('RSV-0099');
  });

  it('aisla caches offline entre tenants al cambiar de empresa en sesion', () => {
    const auth = TestBed.inject(AuthService);
    const cu25 = TestBed.inject(CU25DescargarCatalogoOfflineController);
    const catalogo = TestBed.inject(CatalogoService);
    const inventario = TestBed.inject(InventarioService);

    // Sembrar cache perteneciente a tenant Zara
    localStorage.setItem(
      'catalogo_offline_cache',
      JSON.stringify({
        empresa_id: 'emp-zara',
        sucursales: [{ id: 'suc-zara-1', nombre: 'Zara Central' }],
        prendas: [{ id: 'p-zara-1', codigo: 'Z-1', nombre: 'Abrigo Zara', precio_base: 300 }],
        variantes: [],
        existencias: [],
      }),
    );
    localStorage.setItem(
      'fs_sucursales_cache',
      JSON.stringify({ empresa_id: 'emp-zara', items: [{ id: 'suc-zara-1', nombre: 'Zara Central' }] }),
    );
    localStorage.setItem(
      'fs_offline_catalog_cache',
      JSON.stringify({
        empresa_id: 'emp-zara',
        version: 1,
        updated_at: new Date().toISOString(),
        items: [{ id: 'p-zara-1', empresa_id: 'emp-zara', nombre: 'Abrigo Zara', variantes: [] }],
      }),
    );

    // Iniciar sesion en tenant Demo
    auth.login({ empresa_slug: 'demo', correo: 'cliente@demo.com', password: 'secret' }).subscribe();
    const loginReq = httpMock.expectOne((r) => r.url.endsWith('/auth/login'));
    loginReq.flush({
      access_token: 'tok-demo',
      refresh_token: 'ref-demo',
      token_type: 'bearer',
      expires_in: 3600,
      usuario: {
        id: 'u-demo',
        empresa_id: 'emp-demo',
        rol: 'cliente',
        nombre: 'Cliente Demo',
        correo: 'cliente@demo.com',
        email_verificado: true,
        estado: 'activo',
      },
    });

    // Ningun servicio debe exponer datos cacheados de Zara
    expect(cu25.obtenerSucursalesCacheadas().length).toBe(0);
    expect(inventario.obtenerSucursalesOffline().length).toBe(0);
    expect(catalogo.obtenerPrendasCacheadas().length).toBe(0);
  });
});

