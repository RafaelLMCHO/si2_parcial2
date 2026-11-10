import 'dart:convert';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../features/auth/data/auth_models.dart';
import '../../features/catalogo/data/catalogo_models.dart';

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
      version: 4,
      onCreate: (db, version) async {
        await _createSessionTables(db);
        await _createCatalogoTables(db);
        await _createInventarioTables(db);
        await _createOfflineTables(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await _createCatalogoTables(db);
        }
        if (oldVersion < 3) {
          await _createInventarioTables(db);
        }
        if (oldVersion < 4) {
          await _createOfflineTables(db);
        }
      },
    );
    return _db!;
  }

  Future<void> _createOfflineTables(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS soft_locks (
        id TEXT PRIMARY KEY,
        variante_id TEXT NOT NULL,
        sucursal_id TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        expira_en TEXT NOT NULL,
        creado_en TEXT NOT NULL
      )
    ''');
  }

  Future<void> _createInventarioTables(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS existencias_local (
        empresa_id TEXT NOT NULL,
        sucursal_id TEXT NOT NULL,
        variante_id TEXT NOT NULL,
        stock_disponible INTEGER NOT NULL DEFAULT 0,
        actualizado_en TEXT NOT NULL,
        PRIMARY KEY (empresa_id, sucursal_id, variante_id)
      )
    ''');
  }

  Future<void> _createSessionTables(Database db) async {
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
  }

  Future<void> _createCatalogoTables(Database db) async {
    await db.execute('''
      CREATE TABLE catalogo_cache (
        empresa_slug TEXT NOT NULL,
        prenda_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        version INTEGER NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (empresa_slug, prenda_id)
      )
    ''');
    await db.execute('''
      CREATE INDEX idx_catalogo_cache_empresa
      ON catalogo_cache (empresa_slug)
    ''');
    await db.execute('''
      CREATE TABLE catalogo_auxiliares_cache (
        empresa_slug TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');
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

  Future<void> saveCatalogoSnapshot({
    required String empresaSlug,
    required int version,
    required List<Prenda> items,
  }) async {
    final db = await database;
    final updatedAt = DateTime.now().toIso8601String();
    await db.transaction((txn) async {
      await txn.delete(
        'catalogo_cache',
        where: 'empresa_slug = ?',
        whereArgs: [empresaSlug],
      );
      final batch = txn.batch();
      for (final item in items) {
        batch.insert('catalogo_cache', {
          'empresa_slug': empresaSlug,
          'prenda_id': item.id,
          'payload': jsonEncode(item.toJson()),
          'version': version,
          'updated_at': updatedAt,
        }, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
    });
  }

  Future<CatalogoSnapshot?> readCatalogoSnapshot(String empresaSlug) async {
    final db = await database;
    final rows = await db.query(
      'catalogo_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
      orderBy: 'prenda_id ASC',
    );
    if (rows.isEmpty) {
      return null;
    }

    final items = <Prenda>[];
    var version = 0;
    DateTime? updatedAt;
    for (final row in rows) {
      final payload = row['payload']?.toString();
      if (payload == null || payload.isEmpty) {
        continue;
      }
      try {
        final decoded = jsonDecode(payload);
        if (decoded is Map) {
          items.add(Prenda.fromJson(Map<String, dynamic>.from(decoded)));
        }
      } catch (_) {
        continue;
      }
      final rowVersion = int.tryParse(row['version']?.toString() ?? '');
      if (rowVersion != null && rowVersion > version) {
        version = rowVersion;
      }
      updatedAt ??= DateTime.tryParse(row['updated_at']?.toString() ?? '');
    }

    if (items.isEmpty) {
      return null;
    }

    return CatalogoSnapshot(
      version: version,
      updatedAt: updatedAt ?? DateTime.now(),
      items: items,
    );
  }

  Future<void> saveCatalogoAuxiliares({
    required String empresaSlug,
    required AuxiliaresCatalogo auxiliares,
  }) async {
    final db = await database;
    await db.insert('catalogo_auxiliares_cache', {
      'empresa_slug': empresaSlug,
      'payload': jsonEncode(auxiliares.toJson()),
      'updated_at': DateTime.now().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<AuxiliaresCatalogo?> readCatalogoAuxiliares(String empresaSlug) async {
    final db = await database;
    final rows = await db.query(
      'catalogo_auxiliares_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    final payload = rows.first['payload']?.toString();
    if (payload == null || payload.isEmpty) {
      return null;
    }
    try {
      final decoded = jsonDecode(payload);
      if (decoded is Map) {
        return AuxiliaresCatalogo.fromJson(Map<String, dynamic>.from(decoded));
      }
    } catch (_) {
      return null;
    }
    return null;
  }

  Future<void> clearCatalogoCache(String empresaSlug) async {
    final db = await database;
    await db.delete(
      'catalogo_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
    );
    await db.delete(
      'catalogo_auxiliares_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
    );
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

  Future<void> registrarOperacionOffline({
    required String id,
    required String tipo,
    required Map<String, dynamic> payload,
    String estado = 'pendiente',
  }) async {
    final db = await database;
    await db.insert('operacion_pendiente', {
      'id': id,
      'tipo': tipo,
      'payload': jsonEncode(payload),
      'estado': estado,
      'creada_en': DateTime.now().toIso8601String(),
      'intentos': 0,
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<List<Map<String, dynamic>>> listarOperacionesOffline() async {
    final db = await database;
    final rows = await db.query('operacion_pendiente', orderBy: 'creada_en DESC');
    return rows.map((r) {
      final map = Map<String, dynamic>.from(r);
      try {
        map['payload'] = jsonDecode(r['payload'] as String);
      } catch (_) {}
      return map;
    }).toList();
  }

  Future<void> actualizarEstadoOperacion(String id, String nuevoEstado) async {
    final db = await database;
    await db.update(
      'operacion_pendiente',
      {'estado': nuevoEstado},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<bool> crearSoftLockLocal({
    required String id,
    required String varianteId,
    required String sucursalId,
    required int cantidad,
    int ttlMinutos = 45,
  }) async {
    final db = await database;
    final ahoraUtc = DateTime.now().toUtc();
    final expiraEn = ahoraUtc
        .add(Duration(minutes: ttlMinutos))
        .toIso8601String();
    await db.insert('soft_locks', {
      'id': id,
      'variante_id': varianteId,
      'sucursal_id': sucursalId,
      'cantidad': cantidad,
      'expira_en': expiraEn,
      'creado_en': ahoraUtc.toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
    return true;
  }

  Future<List<Map<String, dynamic>>> listarSoftLocksActivos() async {
    final db = await database;
    final nowIso = DateTime.now().toUtc().toIso8601String();
    await db.delete(
      'soft_locks',
      where: 'expira_en <= ?',
      whereArgs: [nowIso],
    );
    final rows = await db.query(
      'soft_locks',
      where: 'expira_en > ?',
      whereArgs: [nowIso],
      orderBy: 'creado_en DESC',
    );
    return rows.map((r) => Map<String, dynamic>.from(r)).toList();
  }

  Future<void> eliminarSoftLockLocal(String id) async {
    final db = await database;
    await db.delete(
      'soft_locks',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<List<Map<String, dynamic>>> listarExistenciasLocales() async {
    final db = await database;
    final rows = await db.query(
      'existencias_local',
      orderBy: 'actualizado_en DESC',
    );
    return rows.map((r) => Map<String, dynamic>.from(r)).toList();
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
