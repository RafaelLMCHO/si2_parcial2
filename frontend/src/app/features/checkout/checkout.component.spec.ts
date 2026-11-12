import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { NetworkService } from '../../core/network.service';
import { SessionStoreService } from '../../core/session-store.service';
import { CheckoutComponent } from './checkout.component';

describe('CheckoutComponent (CU-22 y CU-24)', () => {
  let httpMock: HttpTestingController;
  let network: NetworkService;
  let store: SessionStoreService;

  const sucursalA = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1';
  const sucursalB = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2';
  const varianteId = '11111111-1111-1111-1111-111111111601';
  const prendaId = '22222222-2222-2222-2222-222222222201';
  const pagoId = '33333333-3333-3333-3333-333333333301';
  const ventaId = '44444444-4444-4444-4444-444444444401';

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [CheckoutComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    network = TestBed.inject(NetworkService);
    store = TestBed.inject(SessionStoreService);
    store.saveTenant('demo');
    network.markOnline();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  function flushInitialLoad(withStockInSucursalB = true) {
    httpMock.expectOne('/api/v1/carrito').flush({
      id: 'cart-1',
      total: 180,
      items: [
        {
          id: 'item-1',
          variante_id: varianteId,
          sku: 'VES-001-S',
          prenda_nombre: 'Vestido midi',
          talla: 'S',
          color: 'Negro',
          cantidad: 1,
          precio_unitario: 180,
          subtotal: 180,
        },
      ],
    });

    httpMock.expectOne('/api/v1/checkout/direcciones').flush({ items: [] });

    httpMock.expectOne('/api/v1/catalogo/prendas?empresa_slug=demo').flush({
      total: 1,
      version_catalogo: 1,
      items: [
        {
          id: prendaId,
          empresa_id: 'emp-1',
          codigo: 'VES-001',
          nombre: 'Vestido midi',
          genero: 'mujer',
          precio_base: 180,
          moneda: 'BOB',
          categoria_id: 'cat-1',
          estado: 'activa',
          created_at: '',
          updated_at: '',
          variantes: [{ id: varianteId, prenda_id: prendaId, talla_id: 1, color_id: 1, sku: 'VES-001-S', precio_venta: 180, costo: 80, estado: 'activa', created_at: '', updated_at: '' }],
        },
      ],
    });

    httpMock.expectOne(`/api/v1/inventario/prendas/${prendaId}/disponibilidad`).flush({
      prenda_id: prendaId,
      agotado_en_todas: false,
      actualizado_en: '2026-11-11T00:00:00Z',
      sucursales: [
        {
          sucursal_id: sucursalA,
          nombre: 'Sucursal Norte',
          direccion: 'Av 1',
          ciudad: 'La Paz',
          variantes: [{ variante_id: varianteId, sku: 'VES-001-S', talla: 'S', color: 'Negro', stock_disponible: 0 }],
        },
        {
          sucursal_id: sucursalB,
          nombre: 'Sucursal Centro',
          direccion: 'Av 2',
          ciudad: 'Santa Cruz',
          variantes: [{ variante_id: varianteId, sku: 'VES-001-S', talla: 'S', color: 'Negro', stock_disponible: withStockInSucursalB ? 6 : 0 }],
        },
      ],
    });
  }

  it('inicia en recojo con sucursal dinámica con stock, crea orden y concilia pago Stripe hasta paso 4', () => {
    const fixture = TestBed.createComponent(CheckoutComponent);
    const comp = fixture.componentInstance;
    fixture.detectChanges();

    flushInitialLoad(true);

    expect(comp.entregaForm.get('tipo_entrega')?.value).toBe('recojo');
    expect(comp.entregaForm.get('sucursal_id')?.value).toBe(sucursalB);

    comp.iniciarCheckout();
    httpMock.expectOne('/api/v1/checkout/validar').flush({
      subtotal: 180,
      descuento: 0,
      impuesto: 23.4,
      costo_envio: 0,
      total_a_pagar: 203.4,
      sucursal_despacho_id: sucursalB,
      sucursal_despacho_nombre: 'Sucursal Centro',
      cupon_id: null,
      lineas_faltantes: [],
    });

    expect(comp.paso).toBe(2);

    comp.crearOrden();
    const reqOrden = httpMock.expectOne('/api/v1/checkout/ordenes');
    expect(reqOrden.request.headers.has('Idempotency-Key')).toBeTrue();
    expect(reqOrden.request.body).toEqual({
      tipo_entrega: 'recojo',
      sucursal_id: sucursalB,
    });
    reqOrden.flush({
      venta_id: ventaId,
      numero: 'V-00010',
      total_a_pagar: 203.4,
      estado: 'pendiente_pago',
    });

    expect(comp.paso).toBe(3);

    comp.procesarCobroMock();
    const reqIntencion = httpMock.expectOne('/api/v1/pagos/intencion');
    expect(reqIntencion.request.body).toEqual({ venta_id: ventaId });
    reqIntencion.flush({
      pago_id: pagoId,
      client_secret: 'pi_mock_secret',
      publishable_key: 'pk_test_demo',
      monto: 20340,
      moneda: 'usd',
    });

    const reqConciliar = httpMock.expectOne(
      `/api/v1/pagos/${pagoId}/conciliar?payment_method=pm_card_visa`
    );
    expect(reqConciliar.request.method).toBe('POST');
    reqConciliar.flush({
      venta_id: ventaId,
      venta_estado: 'completada',
      pago_id: pagoId,
      pago_estado: 'completado',
      pasarela_id: 'pi_mock_123',
      mensaje_error: null,
    });

    expect(comp.paso).toBe(4);
    expect(comp.errorPago).toBe('');
  });

  it('muestra el error real 503 cuando la pasarela no está configurada y permite reintentar directo sin 422', () => {
    const fixture = TestBed.createComponent(CheckoutComponent);
    const comp = fixture.componentInstance;
    fixture.detectChanges();

    flushInitialLoad(true);

    comp.iniciarCheckout();
    httpMock.expectOne('/api/v1/checkout/validar').flush({
      subtotal: 180,
      descuento: 0,
      impuesto: 23.4,
      costo_envio: 0,
      total_a_pagar: 203.4,
      lineas_faltantes: [],
    });

    comp.crearOrden();
    httpMock.expectOne('/api/v1/checkout/ordenes').flush({
      venta_id: ventaId,
      numero: 'V-00011',
      total_a_pagar: 203.4,
      estado: 'pendiente_pago',
    });

    comp.procesarCobroMock();
    httpMock.expectOne('/api/v1/pagos/intencion').flush(
      { detail: { code: 'PASARELA_NO_CONFIGURADA', message: 'La pasarela de pagos Stripe no está configurada.' } },
      { status: 503, statusText: 'Service Unavailable' }
    );

    expect(comp.paso).toBe(3);
    expect(comp.errorPago).toContain('Stripe');

    // Al reintentar desde pendiente_pago no debe llamar a reintentar-pago (que exige pago_fallido)
    comp.reintentarPago();
    httpMock.expectNone(`/api/v1/checkout/ordenes/${ventaId}/reintentar-pago`);

    httpMock.expectOne('/api/v1/pagos/intencion').flush({
      pago_id: pagoId,
      client_secret: 'pi_mock_secret',
      publishable_key: 'pk_test_demo',
      monto: 20340,
      moneda: 'usd',
    });
    httpMock.expectOne(`/api/v1/pagos/${pagoId}/conciliar?payment_method=pm_card_visa`).flush({
      venta_id: ventaId,
      venta_estado: 'completada',
      pago_id: pagoId,
      pago_estado: 'completado',
    });

    expect(comp.paso).toBe(4);
  });
});
