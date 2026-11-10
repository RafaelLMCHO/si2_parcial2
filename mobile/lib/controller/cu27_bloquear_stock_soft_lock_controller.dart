import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';
import '../core/storage/local_database.dart';

/// CU-27: Bloquear stock local offline con TTL (Soft-Lock temporal de 45 minutos)
class CU27BloquearStockSoftLockController extends ChangeNotifier {
  final LocalDatabase _database;
  final ApiClient? _apiClient;
  bool _loading = false;
  String? _error;
  final Map<String, int> _locksActivos = {};
  List<Map<String, dynamic>> _bloqueos = [];

  CU27BloquearStockSoftLockController(this._database, {this._apiClient});

  bool get loading => _loading;
  String? get error => _error;
  Map<String, int> get locksActivos => _locksActivos;
  List<Map<String, dynamic>> get bloqueos => _bloqueos;

  int _calcularTtlSegundos(String expiraEnIso) {
    final expira = DateTime.tryParse(expiraEnIso);
    if (expira == null) return 0;
    final diff = expira.toUtc().difference(DateTime.now().toUtc()).inSeconds;
    return diff > 0 ? diff : 0;
  }

  void _reconstruirResumen() {
    _locksActivos.clear();
    for (final b in _bloqueos) {
      final varianteId = b['variante_id']?.toString() ?? '';
      final cant = (b['cantidad'] as num?)?.toInt() ?? 0;
      if (varianteId.isNotEmpty) {
        _locksActivos[varianteId] = (_locksActivos[varianteId] ?? 0) + cant;
      }
    }
  }

  Future<void> cargarBloqueosActivos({String? sucursalId}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final locales = await _database.listarSoftLocksActivos();
      final filtradosLocal = sucursalId == null || sucursalId.isEmpty
          ? locales
          : locales.where((r) => r['sucursal_id'] == sucursalId).toList();

      final mapa = <String, Map<String, dynamic>>{};
      for (final item in filtradosLocal) {
        final id = item['id']?.toString() ?? '';
        final expira = item['expira_en']?.toString() ?? '';
        final ttl = _calcularTtlSegundos(expira);
        if (ttl > 0 && id.isNotEmpty) {
          mapa[id] = {
            ...item,
            'origen': 'local',
            'ttl_restante_segundos': ttl,
          };
        }
      }

      if (_apiClient != null) {
        try {
          final query = <String, dynamic>{};
          if (sucursalId != null && sucursalId.isNotEmpty) {
            query['sucursal_id'] = sucursalId;
          }
          final dynamic remotos = await _apiClient.get(
            '/sync/soft-locks',
            query: query,
          );
          if (remotos is List) {
            for (final raw in remotos) {
              if (raw is Map) {
                final m = Map<String, dynamic>.from(raw);
                final id = m['id']?.toString() ?? '';
                if (id.isEmpty) continue;
                mapa[id] = {
                  ...m,
                  'origen': 'servidor',
                  'ttl_restante_segundos':
                      (m['ttl_restante_segundos'] as num?)?.toInt() ??
                      _calcularTtlSegundos(m['expira_en']?.toString() ?? ''),
                };
              }
            }
          }
        } catch (_) {
          // Offline o sesion sin red: mantener solo locks locales SQLite
        }
      }

      _bloqueos = mapa.values.toList()
        ..sort(
          (a, b) => (b['creado_en']?.toString() ?? '').compareTo(
            a['creado_en']?.toString() ?? '',
          ),
        );
      _reconstruirResumen();
    } catch (e) {
      _error = 'Error cargando bloqueos activos: $e';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<bool> bloquearStock({
    required String varianteId,
    required String sucursalId,
    required int cantidad,
    int ttlMinutos = 45,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      var lockId = 'lock-${DateTime.now().millisecondsSinceEpoch}';
      var expiraEn = DateTime.now()
          .add(Duration(minutes: ttlMinutos))
          .toIso8601String();
      var origen = 'local';

      if (_apiClient != null) {
        try {
          final dynamic res = await _apiClient.post('/sync/soft-locks', {
            'variante_id': varianteId,
            'sucursal_id': sucursalId,
            'cantidad': cantidad,
            'ttl_minutos': ttlMinutos,
          });
          if (res is Map) {
            lockId = res['lock_id']?.toString() ?? lockId;
            expiraEn = res['expira_en']?.toString() ?? expiraEn;
            origen = 'servidor';
          }
        } catch (_) {
          // Modo offline: continua guardando en SQLite local
        }
      }

      await _database.crearSoftLockLocal(
        id: lockId,
        varianteId: varianteId,
        sucursalId: sucursalId,
        cantidad: cantidad,
        ttlMinutos: ttlMinutos,
      );

      final item = {
        'id': lockId,
        'variante_id': varianteId,
        'sucursal_id': sucursalId,
        'cantidad': cantidad,
        'expira_en': expiraEn,
        'creado_en': DateTime.now().toIso8601String(),
        'origen': origen,
        'ttl_restante_segundos': ttlMinutos * 60,
      };
      _bloqueos = [item, ..._bloqueos.where((b) => b['id'] != lockId)];
      _reconstruirResumen();
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Error aplicando soft-lock local: $e';
      notifyListeners();
      return false;
    }
  }

  Future<bool> liberarBloqueoPorId(String id) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      if (_apiClient != null) {
        try {
          await _apiClient.delete('/sync/soft-locks/$id');
        } catch (_) {
          // Si es lock unicamente local o no hay red, eliminar local igualmente
        }
      }
      await _database.eliminarSoftLockLocal(id);
      _bloqueos = _bloqueos.where((b) => b['id']?.toString() != id).toList();
      _reconstruirResumen();
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Error liberando bloqueo: $e';
      notifyListeners();
      return false;
    }
  }

  void refrescarTtlVisual() {
    var changed = false;
    final actualizados = <Map<String, dynamic>>[];
    for (final b in _bloqueos) {
      final ttl = _calcularTtlSegundos(b['expira_en']?.toString() ?? '');
      if (ttl > 0) {
        actualizados.add({...b, 'ttl_restante_segundos': ttl});
      } else {
        changed = true;
      }
    }
    if (changed || actualizados.isNotEmpty) {
      _bloqueos = actualizados;
      _reconstruirResumen();
      notifyListeners();
    }
  }

  void liberarLock(String varianteId) {
    _locksActivos.remove(varianteId);
    final ids = _bloqueos
        .where((b) => b['variante_id']?.toString() == varianteId)
        .map((b) => b['id']?.toString() ?? '')
        .where((id) => id.isNotEmpty)
        .toList();
    _bloqueos = _bloqueos
        .where((b) => b['variante_id']?.toString() != varianteId)
        .toList();
    for (final id in ids) {
      _database.eliminarSoftLockLocal(id);
    }
    notifyListeners();
  }
}

