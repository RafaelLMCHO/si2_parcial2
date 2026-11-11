import 'package:dio/dio.dart';
import 'package:fashionstore_mobile/app.dart';
import 'package:fashionstore_mobile/controller/cu34_reporte_generativo_ia_controller.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/network/api_exception.dart';
import 'package:fashionstore_mobile/core/routing/role_permissions.dart';
import 'package:fashionstore_mobile/core/session/session_controller.dart';
import 'package:fashionstore_mobile/core/storage/local_database.dart';
import 'package:fashionstore_mobile/core/storage/secure_session_store.dart';
import 'package:fashionstore_mobile/core/utils/network_status.dart';
import 'package:fashionstore_mobile/core/utils/prenda_image_helper.dart';
import 'package:fashionstore_mobile/core/voice/report_export_saver.dart';
import 'package:fashionstore_mobile/core/voice/voice_input_service.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_models.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_repository.dart';
import 'package:fashionstore_mobile/features/auth/presentation/login_screen.dart';
import 'package:fashionstore_mobile/features/catalogo/data/catalogo_models.dart';
import 'package:fashionstore_mobile/features/catalogo/presentation/detalle_producto_screen.dart';
import 'package:fashionstore_mobile/features/catalogo/presentation/widgets/prenda_card.dart';
import 'package:fashionstore_mobile/features/checkout/presentation/checkout_controller.dart';
import 'package:fashionstore_mobile/features/profile/data/profile_repository.dart';
import 'package:fashionstore_mobile/features/reportes/presentation/reporte_ia_screen.dart';
import 'package:fashionstore_mobile/features/reservas/presentation/reservas_screen.dart';
import 'package:fashionstore_mobile/features/sucursales/presentation/sucursales_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

class _FakeSessionController extends SessionController {
  _FakeSessionController({
    required super.authRepository,
    required super.profileRepository,
    required super.secureStore,
    required super.database,
    required super.networkStatus,
    required this.fakeUser,
    ApiClient? fakeApiClient,
  }) : super(apiClient: fakeApiClient);

  final AppUser fakeUser;

  @override
  AppUser? get user => fakeUser;

  @override
  bool get isAuthenticated => true;
}

class _FakeVoiceInputService implements VoiceInputService {
  _FakeVoiceInputService({this.scriptedFinalText});

  final String? scriptedFinalText;
  bool started = false;
  bool stopped = false;

  @override
  Future<bool> isAvailable() async => true;

  @override
  Future<void> startListening({
    required void Function(String partialText) onPartialResult,
    required void Function(String finalText) onFinalResult,
    required void Function(bool listening) onListeningChanged,
    required void Function(String errorMessage) onError,
    String localeId = 'es-BO',
  }) async {
    started = true;
    onListeningChanged(true);
    if (scriptedFinalText != null) {
      onPartialResult(scriptedFinalText!);
      onListeningChanged(false);
      onFinalResult(scriptedFinalText!);
    }
  }

  @override
  Future<void> stopListening() async {
    stopped = true;
  }

  @override
  void dispose() {}
}

class _FakeReportExportSaver implements ReportExportSaver {
  String? lastSavedFile;

  @override
  Future<String> saveExportFile({
    required String fileName,
    required String mimeType,
    required String contentBase64,
  }) async {
    lastSavedFile = 'Descargas/$fileName';
    return lastSavedFile!;
  }
}

class _FakeApiClient extends ApiClient {
  _FakeApiClient({this.onGet, this.onPost})
    : super(baseUrl: 'http://127.0.0.1:8000/api/v1');

  final Future<dynamic> Function(String path, Map<String, dynamic>? query)?
  onGet;
  final Future<dynamic> Function(
    String path,
    dynamic data,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? query,
  )?
  onPost;

  final List<Map<String, dynamic>> postedCalls = [];

  @override
  Future<dynamic> get(
    String path, {
    Map<String, dynamic>? query,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
    bool rawBytes = false,
  }) async {
    if (onGet != null) {
      return onGet!(path, queryParameters ?? query);
    }
    return <String, dynamic>{};
  }

  @override
  Future<dynamic> post(
    String path, [
    dynamic data,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? query,
  ]) async {
    postedCalls.add({
      'path': path,
      'data': data,
      'headers': headers,
      'query': query,
    });
    if (onPost != null) {
      return onPost!(path, data, headers, query);
    }
    return <String, dynamic>{};
  }
}

SessionController _buildSession({AppUser? user, ApiClient? customApiClient}) {
  final apiClient =
      customApiClient ?? ApiClient(baseUrl: 'http://127.0.0.1:8000/api/v1');
  final network = NetworkStatus()..markOnline();
  final session = user == null
      ? SessionController(
          authRepository: AuthRepository(apiClient.dio),
          profileRepository: ProfileRepository(apiClient.dio),
          secureStore: SecureSessionStore(),
          database: LocalDatabase(),
          networkStatus: network,
          apiClient: apiClient,
        )
      : _FakeSessionController(
          authRepository: AuthRepository(apiClient.dio),
          profileRepository: ProfileRepository(apiClient.dio),
          secureStore: SecureSessionStore(),
          database: LocalDatabase(),
          networkStatus: network,
          fakeUser: user,
          fakeApiClient: apiClient,
        );
  apiClient.tokenProvider = () => session.accessToken;
  apiClient.refreshHandler = session.refreshTokens;
  apiClient.sessionExpiredHandler = session.handleSessionExpired;
  apiClient.networkLostHandler = session.handleNetworkLost;
  return session;
}

Prenda _samplePrenda() {
  return const Prenda(
    id: 'prenda-1',
    codigo: 'P-001',
    nombre: 'Camisa de Lino Azul',
    descripcion: 'Camisa fresca para temporada calida.',
    marca: 'DemoWear',
    genero: 'unisex',
    precioBase: 249.50,
    moneda: 'BOB',
    categoriaId: 'cat-1',
    categoriaNombre: 'Camisas',
    imagenUrl: 'https://cdn.fashionstore.test/camisa.jpg',
    estado: 'activa',
    variantes: [
      VariantePrenda(
        id: 'var-1',
        prendaId: 'prenda-1',
        tallaId: 1,
        tallaNombre: 'M',
        colorId: 1,
        colorNombre: 'Azul',
        colorHex: '#1E3A8A',
        sku: 'SKU-LINO-M-AZ',
        precioVenta: 249.50,
        costo: 120.0,
        estado: 'activa',
      ),
      VariantePrenda(
        id: 'var-2',
        prendaId: 'prenda-1',
        tallaId: 2,
        tallaNombre: 'L',
        colorId: 2,
        colorNombre: 'Blanco',
        colorHex: '#FFFFFF',
        sku: 'SKU-LINO-L-BL',
        precioVenta: 259.50,
        costo: 120.0,
        estado: 'activa',
      ),
    ],
  );
}

void main() {
  testWidgets('el login exige correo y contrasena validos', (tester) async {
    final session = _buildSession();

    await tester.pumpWidget(MaterialApp(home: LoginScreen(session: session)));

    expect(find.text('Iniciar sesion'), findsOneWidget);

    await tester.tap(find.text('Ingresar'));
    await tester.pump();

    expect(find.text('Ingrese su correo.'), findsOneWidget);
    expect(find.text('Minimo 8 caracteres.'), findsOneWidget);
  });

  testWidgets('la app muestra el login cuando no hay sesion', (tester) async {
    final session = _buildSession();
    final router = createTestRouter(session);

    await tester.pumpWidget(FashionStoreApp(session: session, router: router));
    await tester.pumpAndSettle();

    expect(find.text('Iniciar sesion'), findsOneWidget);
  });

  test('SucursalesController soporta limite_plan entero sin crash', () async {
    final fakeApi = _FakeApiClient(
      onGet: (path, query) async {
        expect(path, '/sucursales');
        return {
          'total': 2,
          'activas': 2,
          'limite_plan': 5,
          'items': [
            {
              'id': 'suc-1',
              'nombre': 'Casa Matriz Centro',
              'ciudad_nombre': 'Santa Cruz',
              'direccion': 'Av. Monseñor Rivero #123',
              'telefono': '33445566',
              'es_matriz': true,
              'estado': 'activa',
            },
            {
              'id': 'suc-2',
              'nombre': 'Sucursal Equipetrol',
              'ciudad_nombre': 'Santa Cruz',
              'direccion': 'Calle 7 Oeste',
              'telefono': '33778899',
              'es_matriz': false,
              'estado': 'activa',
            },
          ],
        };
      },
    );

    final ctrl = SucursalesController(fakeApi);
    await ctrl.cargarSucursales();

    expect(ctrl.error, isNull);
    expect(ctrl.loading, isFalse);
    expect(ctrl.limitePlan, 5);
    expect(ctrl.activas, 2);
    expect(ctrl.total, 2);
    expect(ctrl.sucursales.length, 2);
  });

  test('resolvePrendaImageUrl reemplaza cdn.fashionstore.test y mapea categorias', () {
    final camisaUrl = resolvePrendaImageUrl(
      imagenUrl: 'https://cdn.fashionstore.test/camisa.jpg',
      nombre: 'Camisa de Lino Clásica',
      categoriaNombre: 'Camisas',
    );
    expect(camisaUrl, isNot(contains('cdn.fashionstore.test')));
    expect(camisaUrl, contains('images.unsplash.com'));

    final blazerUrl = resolvePrendaImageUrl(
      imagenUrl: null,
      nombre: 'Blazer Ejecutivo',
      categoriaNombre: 'Chaquetas',
    );
    expect(blazerUrl, isNot(camisaUrl));
    expect(blazerUrl, contains('images.unsplash.com'));

    const customUrl = 'https://res.cloudinary.com/demo/image/upload/jacket.jpg';
    expect(
      resolvePrendaImageUrl(imagenUrl: customUrl, nombre: 'Otra prenda'),
      customUrl,
    );

    expect(
      resolvePrendaImageUrl(
        imagenUrl: '',
        nombre: 'Prenda Generica',
        categoriaNombre: 'Otros',
      ),
      kFallbackPrendaImageUrl,
    );
  });

  test('role_permissions oculta modulos y bloquea rutas no autorizadas', () {
    final clienteModules = modulesForRole('cliente').map((m) => m.route).toSet();
    expect(
      clienteModules,
      containsAll(['/catalogo', '/checkout', '/reservas', '/vestidor-virtual']),
    );
    expect(clienteModules.contains('/sucursales'), isFalse);
    expect(clienteModules.contains('/pos'), isFalse);
    expect(clienteModules.contains('/saas'), isFalse);

    expect(canAccessRoute('cliente', '/catalogo/prenda/123'), isTrue);
    expect(canAccessRoute('cliente', '/sucursales'), isFalse);
    expect(canAccessRoute('cliente', '/empleados'), isFalse);

    expect(canAccessRoute('cajero', '/pos'), isTrue);
    expect(canAccessRoute('cajero', '/checkout'), isFalse);
    expect(canAccessRoute('cajero', '/sucursales'), isFalse);

    expect(canAccessRoute('encargado', '/reservas'), isTrue);
    expect(canAccessRoute('encargado', '/sucursales'), isFalse);
    expect(canAccessRoute('encargado', '/reportes/ia'), isFalse);

    expect(canAccessRoute('administrador', '/sucursales'), isTrue);
    expect(canAccessRoute('administrador', '/saas'), isFalse);

    expect(canAccessRoute('superadmin', '/saas'), isTrue);
    expect(canAccessRoute('superadmin', '/auditoria'), isTrue);
    expect(canAccessRoute('superadmin', '/backups'), isTrue);
    expect(canAccessRoute('superadmin', '/catalogo'), isFalse);
    expect(canAccessRoute('superadmin', '/catalogo/prenda/123'), isFalse);
  });

  testWidgets('PrendaCard ejecuta onTap al presionar la tarjeta', (tester) async {
    var tapped = false;
    final prenda = _samplePrenda();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PrendaCard(
            prenda: prenda,
            onTap: () => tapped = true,
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Camisa de Lino Azul'), findsOneWidget);
    expect(find.text('Seleccionar'), findsOneWidget);

    await tester.tap(find.byType(PrendaCard));
    await tester.pump();

    expect(tapped, isTrue);
  });

  testWidgets('DetalleProductoScreen muestra acciones de compra y reserva para cliente', (tester) async {
    final prenda = _samplePrenda();
    final fakeApi = _FakeApiClient(
      onGet: (path, query) async {
        if (path == '/catalogo/prendas/${prenda.id}') {
          return prenda.toJson();
        }
        if (path == '/inventario/prendas/${prenda.id}/disponibilidad') {
          return {
            'prenda_id': prenda.id,
            'agotado_en_todas': false,
            'actualizado_en': '2026-11-10T10:00:00Z',
            'sucursales': [
              {
                'sucursal_id': 'suc-1',
                'nombre': 'Casa Matriz',
                'direccion': 'Av Central 100',
                'ciudad': 'Santa Cruz',
                'variantes': [
                  {
                    'variante_id': 'var-1',
                    'sku': 'SKU-LINO-M-AZ',
                    'talla': 'M',
                    'color': 'Azul',
                    'stock_disponible': 7,
                  },
                ],
              },
            ],
          };
        }
        return {};
      },
      onPost: (path, data, headers, query) async => {'items': [], 'total': 0},
    );

    final clientSession = _buildSession(
      user: const AppUser(
        id: 'u-cli-1',
        nombre: 'Cliente Demo',
        correo: 'cliente@demo.test',
        rol: 'cliente',
        emailVerificado: true,
        estado: 'activo',
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: DetalleProductoScreen(
          apiClient: fakeApi,
          prendaId: prenda.id,
          initialPrenda: prenda,
          session: clientSession,
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('M - Azul'), findsOneWidget);
    expect(find.text('L - Blanco'), findsOneWidget);
    expect(find.text('Stock en tiendas: 7 uds'), findsOneWidget);
    expect(find.text('Agregar al carrito'), findsOneWidget);
    expect(find.text('Comprar ahora'), findsOneWidget);
    expect(find.text('Reservar en tienda'), findsOneWidget);

    await tester.ensureVisible(find.text('Agregar al carrito'));
    await tester.pump();
    await tester.tap(find.text('Agregar al carrito'));
    await tester.pump();

    expect(fakeApi.postedCalls.length, 1);
    expect(fakeApi.postedCalls.first['path'], '/carrito/items');
    expect(fakeApi.postedCalls.first['data'], {
      'variante_id': 'var-1',
      'cantidad': 1,
    });
  });

  testWidgets('DetalleProductoScreen oculta acciones de compra para cajero', (tester) async {
    final prenda = _samplePrenda();
    final fakeApi = _FakeApiClient(
      onGet: (path, query) async => prenda.toJson(),
    );
    final cajeroSession = _buildSession(
      user: const AppUser(
        id: 'u-caj-1',
        nombre: 'Cajero Demo',
        correo: 'cajero@demo.test',
        rol: 'cajero',
        emailVerificado: true,
        estado: 'activo',
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: DetalleProductoScreen(
          apiClient: fakeApi,
          prendaId: prenda.id,
          initialPrenda: prenda,
          session: cajeroSession,
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Agregar al carrito'), findsNothing);
    expect(find.text('Comprar ahora'), findsNothing);
    expect(find.text('Reservar en tienda'), findsNothing);
    expect(find.text('Ver disponibilidad por tienda'), findsOneWidget);
  });

  test('CheckoutController conserva pendingOrder ante 503 PASARELA_NO_CONFIGURADA', () async {
    final fakeApi = _FakeApiClient(
      onGet: (path, query) async {
        if (path == '/carrito') {
          return {
            'id': 'cart-1',
            'items': [
              {
                'id': 'item-1',
                'variante_id': 'var-1',
                'sku': 'SKU-LINO-M-AZ',
                'prenda_nombre': 'Camisa de Lino',
                'talla': 'M',
                'color': 'Azul',
                'cantidad': 1,
                'precio_unitario': 249.5,
                'subtotal': 249.5,
              },
            ],
            'total': 249.5,
          };
        }
        if (path == '/catalogo/prendas') {
          return {
            'total': 1,
            'version_catalogo': 1,
            'items': [_samplePrenda().toJson()],
          };
        }
        if (path == '/inventario/prendas/prenda-1/disponibilidad') {
          return {
            'prenda_id': 'prenda-1',
            'agotado_en_todas': false,
            'actualizado_en': '2026-11-10T10:00:00Z',
            'sucursales': [
              {
                'sucursal_id': 'suc-1',
                'nombre': 'Casa Matriz',
                'direccion': 'Av Central 100',
                'ciudad': 'Santa Cruz',
                'variantes': [
                  {
                    'variante_id': 'var-1',
                    'sku': 'SKU-LINO-M-AZ',
                    'talla': 'M',
                    'color': 'Azul',
                    'stock_disponible': 5,
                  },
                ],
              },
            ],
          };
        }
        return {};
      },
      onPost: (path, data, headers, query) async {
        if (path == '/checkout/validar') {
          return {
            'subtotal': 249.5,
            'descuento': 0,
            'impuesto': 32.44,
            'costo_envio': 0,
            'total_a_pagar': 281.94,
            'lineas_faltantes': [],
          };
        }
        if (path == '/checkout/ordenes') {
          return {
            'venta_id': 'venta-123',
            'numero': 'V-00099',
            'total_a_pagar': 281.94,
            'estado': 'pendiente_pago',
          };
        }
        if (path == '/pagos/intencion') {
          throw DioException(
            requestOptions: RequestOptions(path: path),
            response: Response(
              requestOptions: RequestOptions(path: path),
              statusCode: 503,
              data: {
                'detail': {
                  'code': 'PASARELA_NO_CONFIGURADA',
                  'message': 'La pasarela de pagos Stripe no está configurada.',
                },
              },
            ),
          );
        }
        return {};
      },
    );

    final ctrl = CheckoutController(fakeApi);
    await ctrl.cargarCarrito(empresaSlug: 'demo');

    expect(ctrl.tipoEntrega, 'recojo');
    expect(ctrl.sucursalRetiroId, 'suc-1');

    final resultado = await ctrl.realizarPago();
    expect(resultado, isNull);
    expect(ctrl.pendingOrder, isNotNull);
    expect(ctrl.pendingOrder!['numero'], 'V-00099');
    expect(ctrl.pendingOrderNotice, contains('V-00099'));
  });

  test('ApiException.fromDio extrae detail String y List de FastAPI', () {
    final stringDetailErr = DioException(
      requestOptions: RequestOptions(path: '/reportes/ia/consultar'),
      response: Response(
        requestOptions: RequestOptions(path: '/reportes/ia/consultar'),
        statusCode: 400,
        data: {'detail': 'La consulta no coincide con la whitelist BR-08.'},
      ),
    );
    expect(
      ApiException.fromDio(stringDetailErr).message,
      'La consulta no coincide con la whitelist BR-08.',
    );

    final listDetailErr = DioException(
      requestOptions: RequestOptions(path: '/reportes/ia/consultar'),
      response: Response(
        requestOptions: RequestOptions(path: '/reportes/ia/consultar'),
        statusCode: 422,
        data: {
          'detail': [
            {'msg': 'El prompt debe tener al menos 2 caracteres.'},
          ],
        },
      ),
    );
    expect(
      ApiException.fromDio(listDetailErr).message,
      'El prompt debe tener al menos 2 caracteres.',
    );
  });

  test('CU34ReporteGenerativoIaController formatea error limpio ante HTTP 400', () async {
    final fakeApi = _FakeApiClient(
      onPost: (path, data, headers, query) async {
        throw DioException(
          requestOptions: RequestOptions(path: path),
          response: Response(
            requestOptions: RequestOptions(path: path),
            statusCode: 400,
            data: {'detail': 'Consulta fuera de la whitelist autorizada.'},
          ),
        );
      },
    );

    final ctrl = CU34ReporteGenerativoIaController(apiClient: fakeApi);
    final res = await ctrl.solicitarReporteIa(
      prompt: 'drop table',
      canal: 'voz',
    );
    expect(res, isNull);
    expect(ctrl.error, 'Consulta fuera de la whitelist autorizada.');
    expect(ctrl.lastCanal, 'voz');
  });

  testWidgets('ReporteIaScreen ejecuta comando de voz, muestra KPIs, columnas y exporta', (tester) async {
    final fakeApi = _FakeApiClient(
      onPost: (path, data, headers, query) async {
        if (path == '/reportes/ia/consultar') {
          return {
            'consulta_id': '11111111-1111-1111-1111-111111111111',
            'prompt_recibido': 'Mostrame las ventas de septiembre por sucursal',
            'tipo_reporte': 'ventas_por_sucursal',
            'titulo': 'Ventas Consolidadas por Sucursal',
            'resumen_ejecutivo': 'Se consolidaron 12 ventas por Bs. 4500.00.',
            'kpis': {
              'total_facturado_bs': 4500.0,
              'sucursal_lider': 'Casa Matriz',
            },
            'columnas': [
              'Sucursal',
              'Operaciones',
              'Monto Total (Bs.)',
              'Ticket Promedio (Bs.)',
            ],
            'filas': [
              {
                'sucursal': 'Casa Matriz',
                'operaciones': 12,
                'monto_total': 4500.0,
                'ticket_promedio': 375.0,
              },
            ],
            'tipo_grafico': 'barras',
            'datos_grafico': {
              'labels': ['Casa Matriz'],
              'datasets': [
                {
                  'label': 'Ventas',
                  'data': [4500.0],
                },
              ],
            },
            'parametros_aplicados': {},
            'sugerencias': ['¿Cuáles fueron los diez productos más vendidos?'],
            'permitido_exportar': true,
          };
        }
        if (path == '/reportes/ia/exportar') {
          return {
            'reporte_id': '22222222-2222-2222-2222-222222222222',
            'tipo_reporte': 'ventas_por_sucursal',
            'formato': 'xlsx',
            'archivo_url': '/api/v1/reportes/descarga/test.xlsx',
            'tamano_bytes': 1280,
            'generado_en': '2026-11-10T10:00:00Z',
            'contenido_base64': 'UEsDBA==',
          };
        }
        return {};
      },
    );

    final voiceService = _FakeVoiceInputService(
      scriptedFinalText: 'Mostrame las ventas de septiembre por sucursal',
    );
    final exportSaver = _FakeReportExportSaver();
    final session = _buildSession(
      customApiClient: fakeApi,
      user: const AppUser(
        id: 'u-adm-1',
        nombre: 'Admin Demo',
        correo: 'admin@demo.test',
        rol: 'administrador',
        emailVerificado: true,
        estado: 'activo',
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: ReporteIaScreen(
          session: session,
          voiceService: voiceService,
          exportSaver: exportSaver,
        ),
      ),
    );

    await tester.tap(find.text('Comando de voz'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(voiceService.started, isTrue);
    expect(fakeApi.postedCalls.length, 1);
    expect(fakeApi.postedCalls.first['path'], '/reportes/ia/consultar');
    expect(fakeApi.postedCalls.first['data']['canal'], 'voz');

    expect(find.text('Comando de Voz'), findsOneWidget);
    expect(find.text('Ventas Consolidadas por Sucursal'), findsOneWidget);

    final listScrollable = find.byType(Scrollable).first;

    await tester.scrollUntilVisible(
      find.text('Excel'),
      150,
      scrollable: listScrollable,
    );
    await tester.ensureVisible(find.text('Excel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Excel'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(
      fakeApi.postedCalls.any((c) => c['path'] == '/reportes/ia/exportar'),
      isTrue,
    );
    expect(exportSaver.lastSavedFile, contains('.xlsx'));

    await tester.scrollUntilVisible(
      find.text('Indicadores Clave (KPIs)'),
      200,
      scrollable: listScrollable,
    );
    expect(find.text('Indicadores Clave (KPIs)'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.text('Monto Total (Bs.)'),
      200,
      scrollable: listScrollable,
    );
    expect(find.text('Monto Total (Bs.)'), findsOneWidget);
    expect(find.text('4500'), findsWidgets);
  });

  testWidgets('ReservasScreen permite crear reserva directa desde Nueva reserva', (tester) async {
    final prenda = _samplePrenda();
    final List<Map<String, dynamic>> createdReservas = [];

    final fakeApi = _FakeApiClient(
      onGet: (path, query) async {
        if (path == '/reservas/mis-reservas') {
          return {'total': createdReservas.length, 'items': createdReservas};
        }
        if (path == '/catalogo/prendas') {
          return {
            'total': 1,
            'version_catalogo': 1,
            'items': [prenda.toJson()],
          };
        }
        if (path == '/inventario/prendas/${prenda.id}/disponibilidad') {
          return {
            'prenda_id': prenda.id,
            'agotado_en_todas': false,
            'actualizado_en': '2026-11-10T10:00:00Z',
            'sucursales': [
              {
                'sucursal_id': 'suc-1',
                'nombre': 'Casa Matriz',
                'direccion': 'Av Central 100',
                'ciudad': 'Santa Cruz',
                'variantes': [
                  {
                    'variante_id': 'var-1',
                    'sku': 'SKU-LINO-M-AZ',
                    'talla': 'M',
                    'color': 'Azul',
                    'stock_disponible': 4,
                  },
                ],
              },
            ],
          };
        }
        return {};
      },
      onPost: (path, data, headers, query) async {
        if (path == '/reservas') {
          final created = {
            'id': 'rsv-1',
            'codigo': 'RSV-ABC123',
            'estado': 'pendiente_preparacion',
            'sucursal_nombre': 'Casa Matriz',
            'fecha_visita': data['fecha_visita'],
            'items': [
              {
                'variante_id': 'var-1',
                'prenda_nombre': 'Camisa de Lino Azul',
                'talla': 'M',
                'color': 'Azul',
                'cantidad': 1,
              },
            ],
          };
          createdReservas.add(created);
          return created;
        }
        return {};
      },
    );

    await tester.pumpWidget(
      MaterialApp(
        home: ReservasScreen(
          apiClient: fakeApi,
          esEncargado: false,
          rol: 'cliente',
          empresaSlug: 'demo',
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('No hay reservas activas.'), findsOneWidget);

    await tester.tap(find.text('Nueva reserva').first);
    await tester.pumpAndSettle();

    expect(find.text('Nueva Reserva en Probador'), findsOneWidget);
    expect(find.text('Confirmar reserva'), findsOneWidget);

    await tester.ensureVisible(find.text('Confirmar reserva'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar reserva'));
    await tester.pumpAndSettle();

    expect(fakeApi.postedCalls.length, 1);
    expect(fakeApi.postedCalls.first['path'], '/reservas');
    expect(
      fakeApi.postedCalls.first['headers']?['Idempotency-Key'],
      isNotEmpty,
    );
    expect(find.text('Reserva Confirmada'), findsOneWidget);
    expect(find.textContaining('RSV-ABC123'), findsWidgets);
  });

  testWidgets('DetalleProductoScreen y ReservasScreen permiten reservar sin conexion usando cache local', (tester) async {
    Future<void> pumpUntilFound(Finder finder) async {
      for (var i = 0; i < 40; i++) {
        await tester.runAsync(() async {
          await Future<void>.delayed(const Duration(milliseconds: 50));
        });
        await tester.pump();
        if (finder.evaluate().isNotEmpty) {
          return;
        }
      }
    }

    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    final db = LocalDatabase();
    final prenda = _samplePrenda();

    await tester.runAsync(() async {
      await db.open(path: inMemoryDatabasePath);
      await db.saveOfflinePackage('demo', {
        'empresa_id': 'emp-1',
        'sucursales': [
          {
            'id': 'suc-1',
            'nombre': 'Casa Matriz',
            'direccion': 'Av Central 100',
            'ciudad': 'Santa Cruz',
            'es_matriz': true,
          },
        ],
        'prendas': [prenda.toJson()],
        'variantes': [
          {
            'id': 'var-1',
            'prenda_id': prenda.id,
            'sku': 'SKU-LINO-M-AZ',
            'precio_venta': 249.50,
            'talla': 'M',
            'color': 'Azul',
          },
        ],
        'existencias': [
          {
            'variante_id': 'var-1',
            'sucursal_id': 'suc-1',
            'stock_disponible': 6,
          },
        ],
      });
    });

    final offlineApi = _FakeApiClient(
      onGet: (path, query) async {
        throw DioException(
          requestOptions: RequestOptions(path: path),
          type: DioExceptionType.connectionError,
        );
      },
      onPost: (path, data, headers, query) async {
        throw DioException(
          requestOptions: RequestOptions(path: path),
          type: DioExceptionType.connectionError,
        );
      },
    );

    final network = NetworkStatus()..markOffline();
    final session = _FakeSessionController(
      authRepository: AuthRepository(offlineApi.dio),
      profileRepository: ProfileRepository(offlineApi.dio),
      secureStore: SecureSessionStore(),
      database: db,
      networkStatus: network,
      fakeUser: const AppUser(
        id: 'u-cli-off',
        nombre: 'Cliente Offline',
        correo: 'cliente@demo.test',
        rol: 'cliente',
        emailVerificado: true,
        estado: 'activo',
      ),
      fakeApiClient: offlineApi,
    );

    await tester.pumpWidget(
      MaterialApp(
        home: DetalleProductoScreen(
          apiClient: offlineApi,
          prendaId: prenda.id,
          initialPrenda: prenda,
          session: session,
        ),
      ),
    );
    await pumpUntilFound(find.text('Stock local: 6 uds'));

    expect(find.text('Stock local: 6 uds'), findsOneWidget);

    await tester.ensureVisible(find.text('Reservar en tienda'));
    await tester.pump();
    await tester.tap(find.text('Reservar en tienda'));
    await tester.pumpAndSettle();

    expect(
      find.text('No se pudo obtener la lista de sucursales disponibles para esta prenda.'),
      findsNothing,
    );
    expect(find.textContaining('Casa Matriz'), findsWidgets);

    await tester.ensureVisible(find.text('Confirmar reserva'));
    await tester.pump();
    await tester.tap(find.text('Confirmar reserva'));
    await tester.pump();
    await pumpUntilFound(find.text('Reserva Guardada Offline'));

    expect(find.text('Reserva Guardada Offline'), findsOneWidget);
    expect(session.pendingOperations, 1);

    final ops = await tester.runAsync(() => db.listarOperacionesOffline());
    expect(ops, isNotNull);
    expect(ops!.length, 1);
    expect(ops.single['tipo'], 'reserva_offline');
    expect(
      RegExp(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
      ).hasMatch(ops.single['id'].toString()),
      isTrue,
    );

    // ReservasScreen offline muestra la reserva en cola sin pantalla de error
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    await tester.pumpWidget(
      MaterialApp(
        home: ReservasScreen(
          apiClient: offlineApi,
          esEncargado: false,
          rol: 'cliente',
          empresaSlug: 'demo',
          localDatabase: db,
          session: session,
        ),
      ),
    );
    await tester.pump();
    await pumpUntilFound(find.text('pendiente sync'));

    expect(find.text('pendiente sync'), findsOneWidget);
    expect(find.textContaining('Casa Matriz'), findsOneWidget);
    expect(find.textContaining('Camisa de Lino Azul'), findsOneWidget);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.runAsync(() => db.close());
  });
}

GoRouter createTestRouter(SessionController session) {
  return GoRouter(
    initialLocation: '/login',
    refreshListenable: session,
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => LoginScreen(session: session),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) =>
            const Scaffold(body: Text('Perfil de prueba')),
      ),
    ],
  );
}
