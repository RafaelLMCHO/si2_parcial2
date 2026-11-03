import 'package:fashionstore_mobile/core/storage/local_database.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_models.dart';
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
}
