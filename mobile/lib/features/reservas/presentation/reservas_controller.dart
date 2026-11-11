import 'package:flutter/foundation.dart';

import '../../../controller/cu26_registrar_reserva_offline_controller.dart';
import '../../../controller/cu31_sincronizar_operaciones_controller.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/storage/local_database.dart';
import '../../../core/utils/error_mapper.dart';
import '../../catalogo/data/catalogo_models.dart';
import '../../inventario/data/inventario_models.dart';

/// Controlador para CU-19, CU-20, CU-21 y respaldo offline CU-26/CU-31.
class ReservasController extends ChangeNotifier {
  final ApiClient _apiClient;
  final LocalDatabase? _localDatabase;
  final SessionController? _session;
  String? _empresaSlug;

  bool _loading = false;
  bool _submitting = false;
  bool _syncing = false;
  bool _showingOfflineData = false;
  bool _usandoStockLocal = false;
  int _offlinePendingCount = 0;
  String? _error;
  String? _actionError;
  List<dynamic> _reservas = [];

  ReservasController(
    this._apiClient, {
    LocalDatabase? localDatabase,
    SessionController? session,
    String? empresaSlug,
  }) : _localDatabase = localDatabase ?? session?.database,
       _session = session {
    _empresaSlug = empresaSlug;
  }

  bool get loading => _loading;
  bool get submitting => _submitting;
  bool get syncing => _syncing;
  bool get showingOfflineData => _showingOfflineData;
  bool get usandoStockLocal => _usandoStockLocal;
  int get offlinePendingCount => _offlinePendingCount;
  bool get hasOfflinePending => _offlinePendingCount > 0;
  bool get isOnline => _session?.isOnline ?? true;
  String? get error => _error;
  String? get actionError => _actionError;
  List<dynamic> get reservas => _reservas;

  Future<String> _resolveTenant({String? overrideSlug}) async {
    final s = overrideSlug?.trim();
    if (s != null && s.isNotEmpty) return s;
    final fromField = _empresaSlug?.trim();
    if (fromField != null && fromField.isNotEmpty) return fromField;
    final fromSession = _session?.tenant.trim();
    if (fromSession != null && fromSession.isNotEmpty) return fromSession;
    try {
      return (await _localDatabase?.readTenant()) ?? 'demo';
    } catch (_) {
      return 'demo';
    }
  }

  Future<List<Map<String, dynamic>>> _loadLocalPendingReservas() async {
    final db = _localDatabase;
    if (db == null) {
      _offlinePendingCount = 0;
      return const [];
    }
    late final List<Map<String, dynamic>> ops;
    try {
      ops = await db.listarOperacionesOffline();
    } catch (_) {
      _offlinePendingCount = 0;
      return const [];
    }
    final pendientes = ops
        .where(
          (o) =>
              o['tipo']?.toString() == 'reserva_offline' &&
              o['estado']?.toString() != 'confirmada',
        )
        .toList(growable: false);
    _offlinePendingCount = pendientes.length;

    return pendientes.map((op) {
      final rawPayload = op['payload'];
      final payload = rawPayload is Map
          ? Map<String, dynamic>.from(rawPayload)
          : <String, dynamic>{};
      final idStr = op['id']?.toString() ?? '';
      final shortId = idStr.length >= 6
          ? idStr.substring(0, 6).toUpperCase()
          : idStr.toUpperCase();
      final estadoLocal = op['estado']?.toString() ?? 'pendiente';
      final rawItems = (payload['items'] as List<dynamic>? ?? []);
      final items = rawItems
          .whereType<Map>()
          .map((it) {
            final m = Map<String, dynamic>.from(it);
            return {
              'variante_id': m['variante_id']?.toString() ?? '',
              'prenda_nombre': m['prenda_nombre']?.toString().isNotEmpty == true
                  ? m['prenda_nombre'].toString()
                  : 'Prenda (${m['sku'] ?? m['variante_id'] ?? 'offline'})',
              'talla': m['talla']?.toString() ?? '-',
              'color': m['color']?.toString() ?? '-',
              'cantidad': (m['cantidad'] as num?)?.toInt() ?? 1,
            };
          })
          .toList(growable: false);

      return <String, dynamic>{
        'id': idStr,
        'codigo': payload['codigo_local']?.toString() ?? 'RES-OFF-$shortId',
        'estado': estadoLocal == 'en_conflicto'
            ? 'conflicto_sync'
            : 'pendiente_sync',
        'sucursal_id': payload['sucursal_id']?.toString() ?? '',
        'sucursal_nombre':
            payload['sucursal_nombre']?.toString() ??
            'Sucursal local (sin sincronizar)',
        'fecha_visita': payload['fecha_visita'] ?? op['creada_en'],
        'probador': payload['probador'] == true ? 'Pendiente (offline)' : null,
        'items': items,
        'offline_local': true,
        'offline_estado': estadoLocal,
      };
    }).toList(growable: false);
  }

  Future<void> cargarReservas({
    bool esEncargado = false,
    bool soloPorPreparar = true,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    final localPendientes = await _loadLocalPendingReservas();
    if (_session != null && !_session.isOnline && _localDatabase != null) {
      _reservas = localPendientes;
      _showingOfflineData = true;
      _loading = false;
      notifyListeners();
      return;
    }

    try {
      final endpoint = esEncargado
          ? (soloPorPreparar ? '/reservas/por-preparar' : '/reservas')
          : '/reservas/mis-reservas';
      final res = await _apiClient.get(endpoint);
      final remotos = res is Map ? (res['items'] as List<dynamic>? ?? []) : [];
      final remoteIds = remotos
          .whereType<Map>()
          .map((e) => e['id']?.toString() ?? '')
          .toSet();
      final localFiltered = localPendientes
          .where((l) => !remoteIds.contains(l['id']?.toString() ?? ''))
          .toList(growable: false);
      _reservas = [...localFiltered, ...remotos];
      _showingOfflineData = false;
      _loading = false;
    } catch (e) {
      if (isNetworkError(e)) {
        _session?.handleNetworkLost();
      }
      _loading = false;
      if (_localDatabase != null &&
          (isNetworkError(e) || !(_session?.isOnline ?? true))) {
        _reservas = localPendientes;
        _showingOfflineData = true;
        _error = null;
      } else {
        if (localPendientes.isNotEmpty) {
          _reservas = localPendientes;
        }
        _error = ApiException.fromObject(
          e,
          fallback: 'No se pudieron cargar las reservas.',
        ).message;
      }
    }
    notifyListeners();
  }

  Future<List<Prenda>> cargarPrendasCatalogo({String? empresaSlug}) async {
    final tenant = await _resolveTenant(overrideSlug: empresaSlug);
    final query = {'empresa_slug': tenant};

    if (!(_session?.isOnline ?? true) && _localDatabase != null) {
      try {
        final snapshot = await _localDatabase.readCatalogoSnapshot(tenant);
        return snapshot?.items ?? const [];
      } catch (_) {
        return const [];
      }
    }

    try {
      final res = await _apiClient.get(
        '/catalogo/prendas',
        queryParameters: query,
      );
      if (res is Map) {
        return PrendaListResponse.fromJson(
          Map<String, dynamic>.from(res),
        ).items;
      }
      return const [];
    } catch (e) {
      if (isNetworkError(e)) {
        _session?.handleNetworkLost();
      }
      if (_localDatabase != null &&
          (isNetworkError(e) || !(_session?.isOnline ?? true))) {
        try {
          final snapshot = await _localDatabase.readCatalogoSnapshot(tenant);
          if (snapshot != null && snapshot.items.isNotEmpty) {
            return snapshot.items;
          }
        } catch (_) {}
      }
      rethrow;
    }
  }

  Future<List<DisponibilidadSucursal>> cargarDisponibilidadPrenda(
    String prendaId, {
    Prenda? prenda,
  }) async {
    final tenant = await _resolveTenant();

    if ((_session?.isOnline ?? true)) {
      try {
        final res = await _apiClient.get(
          '/inventario/prendas/$prendaId/disponibilidad',
        );
        if (res is Map) {
          final mapRes = Map<String, dynamic>.from(res);
          if (_localDatabase != null && mapRes['sucursales'] is List) {
            try {
              await _localDatabase.saveDisponibilidadPrenda(
                tenant,
                prendaId,
                mapRes,
              );
            } catch (_) {}
          }
          _usandoStockLocal = false;
          return DisponibilidadPrenda.fromJson(mapRes).sucursales;
        }
        _usandoStockLocal = false;
        return const [];
      } catch (e) {
        if (isNetworkError(e)) {
          _session?.handleNetworkLost();
        } else if (!(_session?.isOnline ?? true)) {
          // continúa hacia respaldo local
        } else if (_localDatabase == null) {
          rethrow;
        }
      }
    }

    if (_localDatabase != null) {
      try {
        final local = await _localDatabase.buildDisponibilidadOffline(
          tenant,
          prendaId,
          prenda: prenda,
        );
        _usandoStockLocal = true;
        return local?.sucursales ?? const [];
      } catch (_) {}
    }
    _usandoStockLocal = false;
    return const [];
  }

  Future<Map<String, dynamic>?> crearReservaDetalle({
    required Map<String, dynamic> payload,
    required String idempotencyKey,
    bool esEncargado = false,
    bool soloPorPreparar = true,
    String? sucursalNombre,
    List<Map<String, dynamic>>? itemsMetadata,
  }) async {
    _submitting = true;
    _actionError = null;
    notifyListeners();

    if (!(_session?.isOnline ?? true) && _localDatabase != null) {
      return _registrarReservaOfflineLocal(
        payload: payload,
        sucursalNombre: sucursalNombre,
        itemsMetadata: itemsMetadata,
        esEncargado: esEncargado,
        soloPorPreparar: soloPorPreparar,
      );
    }

    try {
      final res = await _apiClient.post(
        '/reservas',
        payload,
        {'Idempotency-Key': idempotencyKey},
      );
      _submitting = false;
      await cargarReservas(
        esEncargado: esEncargado,
        soloPorPreparar: soloPorPreparar,
      );
      if (res is Map) {
        return Map<String, dynamic>.from(res);
      }
      return <String, dynamic>{};
    } catch (e) {
      if ((isNetworkError(e) || !(_session?.isOnline ?? true)) &&
          _localDatabase != null) {
        _session?.handleNetworkLost();
        return _registrarReservaOfflineLocal(
          payload: payload,
          sucursalNombre: sucursalNombre,
          itemsMetadata: itemsMetadata,
          esEncargado: esEncargado,
          soloPorPreparar: soloPorPreparar,
        );
      }
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo crear la reserva.',
      ).message;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> _registrarReservaOfflineLocal({
    required Map<String, dynamic> payload,
    String? sucursalNombre,
    List<Map<String, dynamic>>? itemsMetadata,
    bool esEncargado = false,
    bool soloPorPreparar = true,
  }) async {
    final db = _localDatabase;
    if (db == null) {
      _submitting = false;
      _actionError = 'No hay almacenamiento local disponible.';
      notifyListeners();
      return null;
    }

    final sucursalId = payload['sucursal_id']?.toString() ?? '';
    final fechaVisita =
        DateTime.tryParse(payload['fecha_visita']?.toString() ?? '') ??
        DateTime.now().add(const Duration(days: 1));
    final items = itemsMetadata ??
        (payload['items'] as List<dynamic>? ?? [])
            .whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList(growable: false);

    final offlineCtrl = CU26RegistrarReservaOfflineController(db);
    try {
      final uuid = await offlineCtrl.registrarReservaOffline(
        sucursalId: sucursalId,
        sucursalNombre: sucursalNombre,
        fechaVisita: fechaVisita,
        probador: true,
        items: items,
      );
      if (uuid == null) {
        _submitting = false;
        _actionError =
            offlineCtrl.error ?? 'No se pudo guardar la reserva offline.';
        notifyListeners();
        return null;
      }

      await _session?.refreshPendingOperations();
      _submitting = false;
      await cargarReservas(
        esEncargado: esEncargado,
        soloPorPreparar: soloPorPreparar,
      );
      return {
        'id': uuid,
        'codigo': 'RES-OFF-${uuid.substring(0, 6).toUpperCase()}',
        'sucursal_id': sucursalId,
        'sucursal_nombre': sucursalNombre ?? 'Sucursal local',
        'fecha_visita': fechaVisita.toUtc().toIso8601String(),
        'estado': 'pendiente_sync',
        'offline': true,
      };
    } finally {
      offlineCtrl.dispose();
    }
  }

  Future<Map<String, int>?> sincronizarPendientes({
    bool esEncargado = false,
    bool soloPorPreparar = true,
  }) async {
    final db = _localDatabase;
    if (db == null) return null;

    _syncing = true;
    _actionError = null;
    notifyListeners();

    final syncCtrl = CU31SincronizarOperacionesController(_apiClient, db);
    try {
      final ok = await syncCtrl.sincronizarLote();
      await _session?.refreshPendingOperations();
      _syncing = false;
      if (!ok) {
        _actionError = syncCtrl.error ?? 'No se pudieron sincronizar reservas.';
        notifyListeners();
        return null;
      }
      await cargarReservas(
        esEncargado: esEncargado,
        soloPorPreparar: soloPorPreparar,
      );
      return {
        'confirmados': syncCtrl.confirmados,
        'conflictos': syncCtrl.conflictos,
      };
    } finally {
      syncCtrl.dispose();
    }
  }

  Future<bool> crearReserva(
    Map<String, dynamic> payload,
    String idempotencyKey, {
    bool esEncargado = false,
    bool soloPorPreparar = true,
  }) async {
    final res = await crearReservaDetalle(
      payload: payload,
      idempotencyKey: idempotencyKey,
      esEncargado: esEncargado,
      soloPorPreparar: soloPorPreparar,
    );
    return res != null;
  }

  Future<bool> cancelarReserva(
    String reservaId, {
    String? motivo,
    bool esEncargado = false,
    bool soloPorPreparar = true,
  }) async {
    _submitting = true;
    _actionError = null;
    notifyListeners();

    try {
      await _apiClient.post(
        '/reservas/$reservaId/cancelar',
        {'motivo': ?motivo},
      );
      _submitting = false;
      await cargarReservas(
        esEncargado: esEncargado,
        soloPorPreparar: soloPorPreparar,
      );
      return true;
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo cancelar la reserva.',
      ).message;
      notifyListeners();
      return false;
    }
  }

  Future<bool> prepararReserva(
    String reservaId,
    String probador, {
    bool soloPorPreparar = true,
  }) async {
    _submitting = true;
    _actionError = null;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/preparar', {
        'probador': probador,
      });
      _submitting = false;
      await cargarReservas(
        esEncargado: true,
        soloPorPreparar: soloPorPreparar,
      );
      return true;
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo marcar la reserva como preparada.',
      ).message;
      notifyListeners();
      return false;
    }
  }

  Future<bool> completarReserva(
    String reservaId, {
    String? motivo,
    bool soloPorPreparar = false,
  }) async {
    _submitting = true;
    _actionError = null;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/completar', {
        'motivo': ?motivo,
      });
      _submitting = false;
      await cargarReservas(
        esEncargado: true,
        soloPorPreparar: soloPorPreparar,
      );
      return true;
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo completar la reserva.',
      ).message;
      notifyListeners();
      return false;
    }
  }
}
