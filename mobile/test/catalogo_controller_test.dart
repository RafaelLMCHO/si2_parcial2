import 'package:dio/dio.dart';
import 'package:fashionstore_mobile/core/storage/local_database.dart';
import 'package:fashionstore_mobile/core/utils/network_status.dart';
import 'package:fashionstore_mobile/features/catalogo/data/catalogo_models.dart';
import 'package:fashionstore_mobile/features/catalogo/data/catalogo_repository.dart';
import 'package:fashionstore_mobile/features/catalogo/presentation/catalogo_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

class _FakeCatalogoRepository extends CatalogoRepository {
  _FakeCatalogoRepository({this.items = const [], this.listError})
    : super(Dio());

  final List<Prenda> items;
  final Object? listError;

  @override
  Future<PrendaListResponse> listarPrendas({
    required String empresaSlug,
    CatalogoFiltros filtros = const CatalogoFiltros(),
    int limit = 50,
    int offset = 0,
  }) async {
    final error = listError;
    if (error != null) {
      throw error;
    }
    return PrendaListResponse(
      total: items.length,
      versionCatalogo: 5,
      items: items,
    );
  }

  @override
  Future<AuxiliaresCatalogo> obtenerAuxiliares(String empresaSlug) async {
    final error = listError;
    if (error != null) {
      throw error;
    }
    return AuxiliaresCatalogo.fromPrendas(items);
  }
}

const _vestido = Prenda(
  id: 'p-1',
  codigo: 'COD-1',
  nombre: 'Vestido floral',
  genero: 'mujer',
  precioBase: 199.90,
  moneda: 'BOB',
  categoriaId: 'cat-1',
  categoriaNombre: 'Vestidos',
  estado: 'activa',
);

const _camisa = Prenda(
  id: 'p-2',
  codigo: 'COD-2',
  nombre: 'Camisa casual',
  genero: 'hombre',
  precioBase: 80,
  moneda: 'BOB',
  categoriaId: 'cat-2',
  categoriaNombre: 'Camisas',
  estado: 'activa',
);

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  test('online guarda snapshot y filtros offline lo consultan', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);
    final network = NetworkStatus()..markOnline();
    final controller = CatalogoController(
      _FakeCatalogoRepository(items: const [_vestido, _camisa]),
      database,
      network,
    );

    await controller.cargarInicial('demo');

    expect(controller.isOffline, isFalse);
    expect(controller.items, hasLength(2));
    expect(controller.auxiliares.categorias, hasLength(2));

    final snapshot = await database.readCatalogoSnapshot('demo');
    expect(snapshot, isNotNull);
    expect(snapshot!.version, 5);
    expect(snapshot.items, hasLength(2));

    network.markOffline();
    await controller.aplicarFiltros(
      const CatalogoFiltros(categoriaId: 'cat-2'),
      'demo',
    );

    expect(controller.isOffline, isTrue);
    expect(controller.items.single.id, 'p-2');
    expect(controller.cacheUpdatedAt, isNotNull);
    expect(controller.sinDatosLocales, isFalse);

    controller.dispose();
    network.dispose();
    await database.close();
  });

  test('offline sin cache informa que falta la descarga local', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);
    final network = NetworkStatus()..markOffline();
    final controller = CatalogoController(
      _FakeCatalogoRepository(items: const [_vestido]),
      database,
      network,
    );

    await controller.cargarInicial('demo');

    expect(controller.isOffline, isTrue);
    expect(controller.sinDatosLocales, isTrue);
    expect(controller.items, isEmpty);

    controller.dispose();
    network.dispose();
    await database.close();
  });

  test('error de red usa el cache y marca el modo offline', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);
    await database.saveCatalogoSnapshot(
      empresaSlug: 'demo',
      version: 3,
      items: const [_vestido],
    );

    final network = NetworkStatus()..markOnline();
    final controller = CatalogoController(
      _FakeCatalogoRepository(
        listError: DioException(
          requestOptions: RequestOptions(path: '/catalogo/prendas'),
          type: DioExceptionType.connectionError,
        ),
      ),
      database,
      network,
    );

    await controller.cargarInicial('demo');

    expect(network.value, isFalse);
    expect(controller.isOffline, isTrue);
    expect(controller.items.single.id, 'p-1');
    expect(controller.versionCatalogo, 3);

    controller.dispose();
    network.dispose();
    await database.close();
  });
}
