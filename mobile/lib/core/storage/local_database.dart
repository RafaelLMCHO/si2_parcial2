import 'dart:convert';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../features/auth/data/auth_models.dart';
import '../../features/catalogo/data/catalogo_models.dart';
import '../../features/inventario/data/inventario_models.dart';

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
      version: 5,
      onCreate: (db, version) async {
        await _createSessionTables(db);
        await _createCatalogoTables(db);
        await _createInventarioTables(db);
        await _createOfflineTables(db);
        await _createOfflineAvailabilityTables(db);
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
        if (oldVersion < 5) {
          await _createOfflineAvailabilityTables(db);
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

  Future<void> _createOfflineAvailabilityTables(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS sucursales_cache (
        empresa_slug TEXT NOT NULL,
        sucursal_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (empresa_slug, sucursal_id)
      )
    ''');
    await db.execute('''
      CREATE TABLE IF NOT EXISTS disponibilidad_cache (
        empresa_slug TEXT NOT NULL,
        prenda_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (empresa_slug, prenda_id)
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
      "SELECT COUNT(*) AS total FROM operacion_pendiente WHERE estado != 'confirmada'",
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
    await db.delete(
      'sucursales_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
    );
    await db.delete(
      'disponibilidad_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
    );
  }

  Future<Prenda?> readPrendaSnapshot(
    String empresaSlug,
    String prendaId,
  ) async {
    final db = await database;
    final rows = await db.query(
      'catalogo_cache',
      where: 'empresa_slug = ? AND prenda_id = ?',
      whereArgs: [empresaSlug, prendaId],
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
        return Prenda.fromJson(Map<String, dynamic>.from(decoded));
      }
    } catch (_) {
      return null;
    }
    return null;
  }

  Future<void> saveSucursalesCache(
    String empresaSlug,
    List<Map<String, dynamic>> sucursales,
  ) async {
    final db = await database;
    final updatedAt = DateTime.now().toUtc().toIso8601String();
    await db.transaction((txn) async {
      await txn.delete(
        'sucursales_cache',
        where: 'empresa_slug = ?',
        whereArgs: [empresaSlug],
      );
      final batch = txn.batch();
      for (final s in sucursales) {
        final sid = (s['id'] ?? s['sucursal_id'])?.toString() ?? '';
        if (sid.isEmpty) continue;
        final normalized = {
          'id': sid,
          'nombre': s['nombre']?.toString() ?? 'Sucursal',
          'direccion': s['direccion']?.toString() ?? '',
          'ciudad': (s['ciudad'] ?? s['ciudad_nombre'])?.toString() ?? '',
          'es_matriz': s['es_matriz'] == true,
        };
        batch.insert('sucursales_cache', {
          'empresa_slug': empresaSlug,
          'sucursal_id': sid,
          'payload': jsonEncode(normalized),
          'updated_at': updatedAt,
        }, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
    });
  }

  Future<List<Map<String, dynamic>>> readSucursalesCache(
    String empresaSlug,
  ) async {
    final db = await database;
    final rows = await db.query(
      'sucursales_cache',
      where: 'empresa_slug = ?',
      whereArgs: [empresaSlug],
    );
    final list = <Map<String, dynamic>>[];
    for (final row in rows) {
      final payload = row['payload']?.toString();
      if (payload == null || payload.isEmpty) continue;
      try {
        final decoded = jsonDecode(payload);
        if (decoded is Map) {
          final map = Map<String, dynamic>.from(decoded);
          map['updated_at'] ??= row['updated_at'];
          list.add(map);
        }
      } catch (_) {}
    }
    list.sort((a, b) {
      final am = a['es_matriz'] == true ? 0 : 1;
      final bm = b['es_matriz'] == true ? 0 : 1;
      if (am != bm) return am.compareTo(bm);
      return (a['nombre']?.toString() ?? '').compareTo(
        b['nombre']?.toString() ?? '',
      );
    });
    return list;
  }

  Future<void> saveExistenciasLocal(
    String empresaId,
    List<Map<String, dynamic>> existencias,
  ) async {
    final db = await database;
    final nowIso = DateTime.now().toUtc().toIso8601String();
    await db.transaction((txn) async {
      await txn.delete(
        'existencias_local',
        where: 'empresa_id = ?',
        whereArgs: [empresaId],
      );
      final batch = txn.batch();
      for (final ex in existencias) {
        final sucId = ex['sucursal_id']?.toString() ?? '';
        final varId = ex['variante_id']?.toString() ?? '';
        if (sucId.isEmpty || varId.isEmpty) continue;
        final stock = (ex['stock_disponible'] as num?)?.toInt() ?? 0;
        batch.insert('existencias_local', {
          'empresa_id': empresaId,
          'sucursal_id': sucId,
          'variante_id': varId,
          'stock_disponible': stock,
          'actualizado_en': nowIso,
        }, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
    });
  }

  Future<void> saveDisponibilidadPrenda(
    String empresaSlug,
    String prendaId,
    Map<String, dynamic> rawJson,
  ) async {
    final db = await database;
    final updatedAt = DateTime.now().toUtc().toIso8601String();
    await db.insert('disponibilidad_cache', {
      'empresa_slug': empresaSlug,
      'prenda_id': prendaId,
      'payload': jsonEncode(rawJson),
      'updated_at': updatedAt,
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<DisponibilidadPrenda?> readDisponibilidadPrenda(
    String empresaSlug,
    String prendaId,
  ) async {
    final db = await database;
    final rows = await db.query(
      'disponibilidad_cache',
      where: 'empresa_slug = ? AND prenda_id = ?',
      whereArgs: [empresaSlug, prendaId],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    final payload = rows.first['payload']?.toString();
    if (payload == null || payload.isEmpty) return null;
    try {
      final decoded = jsonDecode(payload);
      if (decoded is Map) {
        return DisponibilidadPrenda.fromJson(
          Map<String, dynamic>.from(decoded),
          esLocal: true,
        );
      }
    } catch (_) {
      return null;
    }
    return null;
  }

  Future<void> saveOfflinePackage(
    String empresaSlug,
    Map<String, dynamic> pkg,
  ) async {
    final empresaId = pkg['empresa_id']?.toString() ?? empresaSlug;
    final rawSucursales = (pkg['sucursales'] as List<dynamic>? ?? [])
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList(growable: false);
    if (rawSucursales.isNotEmpty) {
      await saveSucursalesCache(empresaSlug, rawSucursales);
    }

    final rawExistencias = (pkg['existencias'] as List<dynamic>? ?? [])
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList(growable: false);
    if (rawExistencias.isNotEmpty) {
      await saveExistenciasLocal(empresaId, rawExistencias);
    }

    final rawPrendas = (pkg['prendas'] as List<dynamic>? ?? [])
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList(growable: false);
    final rawVariantes = (pkg['variantes'] as List<dynamic>? ?? [])
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList(growable: false);

    if (rawPrendas.isEmpty) return;

    final existing = await readCatalogoSnapshot(empresaSlug);
    final existingById = <String, Prenda>{
      if (existing != null)
        for (final p in existing.items) p.id: p,
    };

    final variantesByPrenda = <String, List<VariantePrenda>>{};
    for (final v in rawVariantes) {
      final pId = v['prenda_id']?.toString() ?? '';
      if (pId.isEmpty) continue;
      final normalizedVar = <String, dynamic>{
        ...v,
        'talla_nombre': v['talla_nombre'] ?? v['talla'],
        'color_nombre': v['color_nombre'] ?? v['color'],
      };
      variantesByPrenda
          .putIfAbsent(pId, () => <VariantePrenda>[])
          .add(VariantePrenda.fromJson(normalizedVar));
    }

    final mergedItems = <Prenda>[];
    for (final p in rawPrendas) {
      final pId = p['id']?.toString() ?? '';
      if (pId.isEmpty) continue;
      final prev = existingById[pId];
      final pkgVars = variantesByPrenda[pId] ?? const <VariantePrenda>[];
      final finalVars = pkgVars.isNotEmpty
          ? pkgVars
          : (prev?.variantes ?? const <VariantePrenda>[]);
      mergedItems.add(
        Prenda(
          id: pId,
          empresaId: p['empresa_id']?.toString() ?? prev?.empresaId,
          codigo: p['codigo']?.toString() ?? prev?.codigo ?? '',
          nombre: p['nombre']?.toString() ?? prev?.nombre ?? '',
          descripcion: p['descripcion']?.toString() ?? prev?.descripcion,
          marca: p['marca']?.toString() ?? prev?.marca,
          genero: p['genero']?.toString() ?? prev?.genero ?? 'unisex',
          precioBase:
              (p['precio_base'] as num?)?.toDouble() ??
              double.tryParse(p['precio_base']?.toString() ?? '') ??
              prev?.precioBase ??
              0,
          moneda: p['moneda']?.toString() ?? prev?.moneda ?? 'BOB',
          categoriaId: p['categoria_id']?.toString() ?? prev?.categoriaId ?? '',
          categoriaNombre:
              p['categoria_nombre']?.toString() ?? prev?.categoriaNombre,
          temporadaId: p['temporada_id']?.toString() ?? prev?.temporadaId,
          temporadaNombre:
              p['temporada_nombre']?.toString() ?? prev?.temporadaNombre,
          coleccionId: p['coleccion_id']?.toString() ?? prev?.coleccionId,
          coleccionNombre:
              p['coleccion_nombre']?.toString() ?? prev?.coleccionNombre,
          proveedorId: p['proveedor_id']?.toString() ?? prev?.proveedorId,
          proveedorNombre:
              p['proveedor_nombre']?.toString() ?? prev?.proveedorNombre,
          imagenUrl: p['imagen_url']?.toString() ?? prev?.imagenUrl,
          estado: p['estado']?.toString() ?? prev?.estado ?? 'activa',
          variantes: finalVars,
        ),
      );
    }

    if (mergedItems.isNotEmpty) {
      await saveCatalogoSnapshot(
        empresaSlug: empresaSlug,
        version: existing?.version ?? 1,
        items: mergedItems,
      );
    }
  }

  Future<DisponibilidadPrenda?> buildDisponibilidadOffline(
    String empresaSlug,
    String prendaId, {
    Prenda? prenda,
  }) async {
    final cachedDisp = await readDisponibilidadPrenda(empresaSlug, prendaId);
    final cachedSucursales = await readSucursalesCache(empresaSlug);
    final targetPrenda =
        prenda ?? await readPrendaSnapshot(empresaSlug, prendaId);
    final existencias = await listarExistenciasLocales();
    final activeLocks = await listarSoftLocksActivos();

    final lockMap = <String, int>{};
    for (final l in activeLocks) {
      final suc = l['sucursal_id']?.toString() ?? '';
      final varId = l['variante_id']?.toString() ?? '';
      if (suc.isEmpty || varId.isEmpty) continue;
      final key = '$suc|$varId';
      lockMap[key] = (lockMap[key] ?? 0) + ((l['cantidad'] as num?)?.toInt() ?? 0);
    }

    int applySoftLock(String sucId, String varId, int rawStock) {
      final locked = lockMap['$sucId|$varId'] ?? 0;
      final net = rawStock - locked;
      return net > 0 ? net : 0;
    }

    // Prefer cached /disponibilidad when we lack CU-25 branch/stock package or when cachedDisp is populated and no CU-25 existencias apply
    final variantIds = (targetPrenda?.variantes ?? const <VariantePrenda>[])
        .map((v) => v.id)
        .toSet();
    final relevantExistencias = existencias
        .where((ex) => variantIds.contains(ex['variante_id']?.toString() ?? ''))
        .toList(growable: false);

    if (cachedDisp != null &&
        cachedDisp.sucursales.isNotEmpty &&
        (cachedSucursales.isEmpty || relevantExistencias.isEmpty)) {
      final adjustedSucursales = cachedDisp.sucursales
          .map(
            (s) => DisponibilidadSucursal(
              sucursalId: s.sucursalId,
              nombre: s.nombre,
              direccion: s.direccion,
              ciudad: s.ciudad,
              variantes: s.variantes
                  .map(
                    (v) => DisponibilidadVariante(
                      varianteId: v.varianteId,
                      sku: v.sku,
                      talla: v.talla,
                      color: v.color,
                      stockDisponible: applySoftLock(
                        s.sucursalId,
                        v.varianteId,
                        v.stockDisponible,
                      ),
                    ),
                  )
                  .toList(growable: false),
            ),
          )
          .toList(growable: false);
      final totalAll = adjustedSucursales.fold<int>(
        0,
        (sum, s) =>
            sum + s.variantes.fold<int>(0, (vs, v) => vs + v.stockDisponible),
      );
      return DisponibilidadPrenda(
        prendaId: prendaId,
        agotadoEnTodas: adjustedSucursales.isNotEmpty && totalAll <= 0,
        actualizadoEn: cachedDisp.actualizadoEn,
        sucursales: adjustedSucursales,
        esLocal: true,
      );
    }

    if (cachedSucursales.isEmpty) {
      return cachedDisp;
    }

    final stockMap = <String, int>{};
    String? latestActualizado;
    for (final ex in relevantExistencias) {
      final suc = ex['sucursal_id']?.toString() ?? '';
      final varId = ex['variante_id']?.toString() ?? '';
      if (suc.isEmpty || varId.isEmpty) continue;
      stockMap['$suc|$varId'] = (ex['stock_disponible'] as num?)?.toInt() ?? 0;
      latestActualizado ??= ex['actualizado_en']?.toString();
    }

    final cachedBranchById = <String, DisponibilidadSucursal>{
      if (cachedDisp != null)
        for (final s in cachedDisp.sucursales) s.sucursalId: s,
    };

    var hasAnyStockRecord = relevantExistencias.isNotEmpty;
    var anyPositive = false;
    final sucursales = <DisponibilidadSucursal>[];
    for (final s in cachedSucursales) {
      final sucId = s['id']?.toString() ?? '';
      if (sucId.isEmpty) continue;
      final cachedBranch = cachedBranchById[sucId];
      final branchVariantes = <DisponibilidadVariante>[];
      if (targetPrenda != null && targetPrenda.variantes.isNotEmpty) {
        for (final v in targetPrenda.variantes) {
          final key = '$sucId|${v.id}';
          var rawStock = stockMap[key];
          if (rawStock == null && cachedBranch != null) {
            for (final cv in cachedBranch.variantes) {
              if (cv.varianteId == v.id) {
                rawStock = cv.stockDisponible;
                hasAnyStockRecord = true;
                break;
              }
            }
          }
          final finalStock = applySoftLock(sucId, v.id, rawStock ?? 0);
          if (finalStock > 0) anyPositive = true;
          branchVariantes.add(
            DisponibilidadVariante(
              varianteId: v.id,
              sku: v.sku,
              talla: v.tallaNombre ?? '',
              color: v.colorNombre ?? '',
              stockDisponible: finalStock,
            ),
          );
        }
      } else if (cachedBranch != null) {
        for (final cv in cachedBranch.variantes) {
          final finalStock = applySoftLock(
            sucId,
            cv.varianteId,
            cv.stockDisponible,
          );
          if (finalStock > 0) anyPositive = true;
          hasAnyStockRecord = true;
          branchVariantes.add(
            DisponibilidadVariante(
              varianteId: cv.varianteId,
              sku: cv.sku,
              talla: cv.talla,
              color: cv.color,
              stockDisponible: finalStock,
            ),
          );
        }
      }

      sucursales.add(
        DisponibilidadSucursal(
          sucursalId: sucId,
          nombre: s['nombre']?.toString() ?? 'Sucursal',
          direccion: s['direccion']?.toString() ?? '',
          ciudad: s['ciudad']?.toString() ?? '',
          variantes: branchVariantes,
        ),
      );
    }

    return DisponibilidadPrenda(
      prendaId: prendaId,
      agotadoEnTodas: hasAnyStockRecord && !anyPositive,
      actualizadoEn:
          latestActualizado ??
          cachedDisp?.actualizadoEn ??
          (cachedSucursales.first['updated_at']?.toString() ??
              DateTime.now().toUtc().toIso8601String()),
      sucursales: sucursales,
      esLocal: true,
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
