import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../features/auth/data/auth_models.dart';

class LocalDatabase {
  Database? _db;

  Future<Database> get database async {
    final db = _db;
    if (db != null) {
      return db;
    }
    return open();
  }

  Future<Database> open({String? path}) async {
    if (_db != null) {
      return _db!;
    }

    final databasePath =
        path ?? p.join(await getDatabasesPath(), 'fashionstore.db');
    _db = await openDatabase(
      databasePath,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE usuario_cache (
            id TEXT PRIMARY KEY,
            empresa_id TEXT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            telefono TEXT,
            email_verificado INTEGER NOT NULL,
            estado TEXT NOT NULL,
            rol TEXT NOT NULL,
            sucursal_id TEXT,
            ultimo_acceso TEXT,
            created_at TEXT,
            cached_at TEXT NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE tenant_cache (
            slug TEXT PRIMARY KEY,
            cached_at TEXT NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE operacion_pendiente (
            id TEXT PRIMARY KEY,
            tipo TEXT NOT NULL,
            payload TEXT NOT NULL,
            estado TEXT NOT NULL,
            creada_en TEXT NOT NULL,
            intentos INTEGER NOT NULL DEFAULT 0
          )
        ''');
      },
    );
    return _db!;
  }

  Future<void> saveUser(AppUser user) async {
    final db = await database;
    final map = user.toJson();
    map['email_verificado'] = user.emailVerificado ? 1 : 0;
    map['cached_at'] = DateTime.now().toIso8601String();
    await db.insert(
      'usuario_cache',
      map,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<AppUser?> readUser() async {
    final db = await database;
    final rows = await db.query('usuario_cache', limit: 1);
    if (rows.isEmpty) {
      return null;
    }
    return _userFromRow(rows.first);
  }

  Future<void> saveTenant(String slug) async {
    final db = await database;
    await db.insert('tenant_cache', {
      'slug': slug,
      'cached_at': DateTime.now().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<String?> readTenant() async {
    final db = await database;
    final rows = await db.query('tenant_cache', limit: 1);
    if (rows.isEmpty) {
      return null;
    }
    return rows.first['slug']?.toString();
  }

  Future<void> saveLastSync(DateTime value) async {
    final db = await database;
    await db.insert('sync_meta', {
      'key': 'last_sync',
      'value': value.toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<DateTime?> readLastSync() async {
    final db = await database;
    final rows = await db.query(
      'sync_meta',
      where: 'key = ?',
      whereArgs: ['last_sync'],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return DateTime.tryParse(rows.first['value']?.toString() ?? '');
  }

  Future<int> pendingOperationsCount() async {
    final db = await database;
    final rows = await db.rawQuery(
      'SELECT COUNT(*) AS total FROM operacion_pendiente',
    );
    return (rows.first['total'] as num?)?.toInt() ?? 0;
  }

  Future<void> clearUserCache() async {
    final db = await database;
    await db.delete('usuario_cache');
    await db.delete('sync_meta');
  }

  Future<void> clearAllExceptQueue() async {
    final db = await database;
    await db.delete('usuario_cache');
    await db.delete('tenant_cache');
    await db.delete('sync_meta');
  }

  Future<void> close() async {
    await _db?.close();
    _db = null;
  }

  AppUser _userFromRow(Map<String, Object?> row) {
    return AppUser(
      id: row['id'].toString(),
      empresaId: row['empresa_id']?.toString(),
      nombre: row['nombre']?.toString() ?? '',
      correo: row['correo']?.toString() ?? '',
      telefono: row['telefono']?.toString(),
      emailVerificado: (row['email_verificado'] as num?)?.toInt() == 1,
      estado: row['estado']?.toString() ?? '',
      rol: row['rol']?.toString() ?? '',
      sucursalId: row['sucursal_id']?.toString(),
      ultimoAcceso: DateTime.tryParse(row['ultimo_acceso']?.toString() ?? ''),
      createdAt: DateTime.tryParse(row['created_at']?.toString() ?? ''),
    );
  }
}
