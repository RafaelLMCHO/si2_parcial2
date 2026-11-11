import 'package:fashionstore_mobile/controller/cu26_registrar_reserva_offline_controller.dart';
import 'package:fashionstore_mobile/core/storage/local_database.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_models.dart';
import 'package:fashionstore_mobile/features/catalogo/data/catalogo_models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  test('guarda usuario, tenant y conserva la cola offline', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);

    const user = AppUser(
      id: 'u-1',
      empresaId: 'e-1',
      nombre: 'Cliente Demo',
      correo: 'cliente@demo.test',
      telefono: '70000000',
      emailVerificado: true,
      estado: 'activo',
      rol: 'cliente',
    );

    await database.saveUser(user);
    await database.saveTenant('demo');

    final cached = await database.readUser();
    expect(cached?.id, 'u-1');
    expect(cached?.nombre, 'Cliente Demo');
    expect(cached?.emailVerificado, isTrue);
    expect(await database.readTenant(), 'demo');
    expect(await database.pendingOperationsCount(), 0);

    await database.clearUserCache();
    expect(await database.readUser(), isNull);
    expect(await database.readTenant(), 'demo');

    await database.close();
  });

  test('guarda, reemplaza y aisla el catalogo por tenant', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);

    const prenda = Prenda(
      id: 'p-1',
      codigo: 'COD-1',
      nombre: 'Vestido floral',
      genero: 'mujer',
      precioBase: 199.90,
      moneda: 'BOB',
      categoriaId: 'cat-1',
      categoriaNombre: 'Vestidos',
      estado: 'activa',
      variantes: [
        VariantePrenda(
          id: 'v-1',
          prendaId: 'p-1',
          tallaId: 2,
          tallaNombre: 'M',
          colorId: 5,
          colorNombre: 'Rojo',
          colorHex: '#FF0000',
          sku: 'SKU-1',
          precioVenta: 210.50,
          costo: 100,
          estado: 'activa',
        ),
      ],
    );

    await database.saveCatalogoSnapshot(
      empresaSlug: 'demo',
      version: 7,
      items: const [prenda],
    );
    await database.saveCatalogoAuxiliares(
      empresaSlug: 'demo',
      auxiliares: AuxiliaresCatalogo.fromPrendas(const [prenda]),
    );

    final snapshot = await database.readCatalogoSnapshot('demo');
    expect(snapshot, isNotNull);
    expect(snapshot!.version, 7);
    expect(snapshot.items.single.id, 'p-1');
    expect(snapshot.items.single.precioBase, 199.90);
    expect(snapshot.items.single.tallasDisponibles, contains('M'));

    final auxiliares = await database.readCatalogoAuxiliares('demo');
    expect(auxiliares, isNotNull);
    expect(auxiliares!.categorias.single.id, 'cat-1');
    expect(auxiliares.colores.single.nombre, 'Rojo');
    expect(auxiliares.tallas.single.nombre, 'M');

    expect(await database.readCatalogoSnapshot('otra-tienda'), isNull);
    expect(await database.readCatalogoAuxiliares('otra-tienda'), isNull);

    const prendaNueva = Prenda(
      id: 'p-2',
      codigo: 'COD-2',
      nombre: 'Camisa',
      genero: 'hombre',
      precioBase: 80,
      moneda: 'BOB',
      categoriaId: 'cat-2',
      estado: 'activa',
    );
    await database.saveCatalogoSnapshot(
      empresaSlug: 'demo',
      version: 8,
      items: const [prendaNueva],
    );

    final reemplazado = await database.readCatalogoSnapshot('demo');
    expect(reemplazado!.version, 8);
    expect(reemplazado.items.single.id, 'p-2');

    await database.clearCatalogoCache('demo');
    expect(await database.readCatalogoSnapshot('demo'), isNull);
    expect(await database.readCatalogoAuxiliares('demo'), isNull);

    await database.close();
  });

  test('crea, lista, purga expirados y libera soft-locks CU-27', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);

    await database.crearSoftLockLocal(
      id: 'lock-activo',
      varianteId: 'v-1',
      sucursalId: 's-1',
      cantidad: 2,
      ttlMinutos: 45,
    );
    await database.crearSoftLockLocal(
      id: 'lock-expirado',
      varianteId: 'v-2',
      sucursalId: 's-1',
      cantidad: 1,
      ttlMinutos: -5,
    );

    final activos = await database.listarSoftLocksActivos();
    expect(activos.length, 1);
    expect(activos.single['id'], 'lock-activo');
    expect(activos.single['cantidad'], 2);

    await database.eliminarSoftLockLocal('lock-activo');
    expect(await database.listarSoftLocksActivos(), isEmpty);

    await database.close();
  });

  test('CU-25/CU-18 guarda sucursales y existencias y reconstruye disponibilidad offline', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);

    await database.saveOfflinePackage('demo', {
      'empresa_id': 'emp-1',
      'sucursales': [
        {
          'id': 'suc-1',
          'nombre': 'Casa Matriz',
          'direccion': 'Av Central 100',
          'ciudad': 'Santa Cruz',
          'es_matriz': true,
        },
        {
          'id': 'suc-2',
          'nombre': 'Equipetrol',
          'direccion': 'Calle 7',
          'ciudad': 'Santa Cruz',
          'es_matriz': false,
        },
      ],
      'prendas': [
        {
          'id': 'prenda-1',
          'codigo': 'FS-VES-001',
          'nombre': 'Vestido midi',
          'descripcion': 'Vestido midi de lino',
          'precio_base': 180.0,
          'categoria_id': 'cat-1',
        },
      ],
      'variantes': [
        {
          'id': 'var-1',
          'prenda_id': 'prenda-1',
          'sku': 'FS-VES-001-XS-AZU',
          'precio_venta': 180.0,
          'talla': 'XS',
          'color': 'Azul Marino',
          'color_hex': '#1E3A8A',
        },
      ],
      'existencias': [
        {
          'variante_id': 'var-1',
          'sucursal_id': 'suc-1',
          'stock_disponible': 5,
        },
        {
          'variante_id': 'var-1',
          'sucursal_id': 'suc-2',
          'stock_disponible': 2,
        },
      ],
    });

    final disp = await database.buildDisponibilidadOffline('demo', 'prenda-1');
    expect(disp, isNotNull);
    expect(disp!.esLocal, isTrue);
    expect(disp.sucursales.length, 2);
    expect(disp.sucursales.first.nombre, 'Casa Matriz');
    expect(disp.sucursales.first.variantes.single.stockDisponible, 5);

    // El soft-lock local descuenta temporalmente el disponible estimado
    await database.crearSoftLockLocal(
      id: 'lock-1',
      varianteId: 'var-1',
      sucursalId: 'suc-1',
      cantidad: 2,
    );
    final dispConLock = await database.buildDisponibilidadOffline(
      'demo',
      'prenda-1',
    );
    expect(dispConLock!.sucursales.first.variantes.single.stockDisponible, 3);

    await database.close();
  });

  test('CU-26 genera UUID v4 valido y pendingOperationsCount excluye confirmadas', () async {
    final database = LocalDatabase();
    await database.open(path: inMemoryDatabasePath);
    final cu26 = CU26RegistrarReservaOfflineController(database);

    final id = await cu26.registrarReservaOffline(
      sucursalId: '11111111-1111-1111-1111-111111111101',
      sucursalNombre: 'Casa Matriz',
      fechaVisita: DateTime.now().add(const Duration(days: 1)),
      probador: true,
      items: [
        {'variante_id': '22222222-2222-2222-2222-222222222201', 'cantidad': 1},
      ],
    );

    final uuidRegex = RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    );
    expect(id, isNotNull);
    expect(uuidRegex.hasMatch(id!), isTrue);
    expect(await database.pendingOperationsCount(), 1);

    await database.actualizarEstadoOperacion(id, 'confirmada');
    expect(await database.pendingOperationsCount(), 0);

    cu26.dispose();
    await database.close();
  });
}
