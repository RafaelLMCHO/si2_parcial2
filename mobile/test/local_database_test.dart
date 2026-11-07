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
}
