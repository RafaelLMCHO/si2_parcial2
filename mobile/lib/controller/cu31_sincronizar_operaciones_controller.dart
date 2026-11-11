import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';
import '../core/storage/local_database.dart';

/// CU-31: Sincronizar operaciones pendientes (idempotencia RNF05)
class CU31SincronizarOperacionesController extends ChangeNotifier {
  final ApiClient _apiClient;
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  int _confirmados = 0;
  int _conflictos = 0;

  CU31SincronizarOperacionesController(this._apiClient, this._database);

  bool get loading => _loading;
  String? get error => _error;
  int get confirmados => _confirmados;
  int get conflictos => _conflictos;

  Future<bool> sincronizarLote() async {
    _loading = true;
    _error = null;
    _confirmados = 0;
    _conflictos = 0;
    notifyListeners();

    try {
      final ops = await _database.listarOperacionesOffline();
      final pendientes = ops.where((o) => o['estado'] == 'pendiente').toList();

      if (pendientes.isEmpty) {
        _loading = false;
        notifyListeners();
        return true;
      }

      // Marcar en tránsito como 'enviada'
      for (var op in pendientes) {
        await _database.actualizarEstadoOperacion(op['id'].toString(), 'enviada');
      }

      final payload = {
        'dispositivo_id': 'FLUTTER-APP-01',
        'operaciones': pendientes.map((o) {
          final rawPayload = o['payload'];
          final payloadMap = rawPayload is Map
              ? Map<String, dynamic>.from(rawPayload)
              : <String, dynamic>{};
          return {
            'id': o['id'],
            'tipo': o['tipo'],
            'sucursal_id':
                payloadMap['sucursal_id'] ??
                '11111111-1111-1111-1111-111111111101',
            'payload': payloadMap,
            'creada_en': o['creada_en'],
            'idempotency_key': 'IDEMP-${o['id']}',
          };
        }).toList(),
      };

      try {
        final res = await _apiClient.post('/sync', payload);
        final confList = (res['confirmados'] as List<dynamic>? ?? []);
        final conflList = (res['conflictos'] as List<dynamic>? ?? []);

        for (var id in confList) {
          await _database.actualizarEstadoOperacion(id.toString(), 'confirmada');
        }
        for (var c in conflList) {
          await _database.actualizarEstadoOperacion(c['id'].toString(), 'en_conflicto');
        }

        _confirmados = confList.length;
        _conflictos = conflList.length;
        _loading = false;
        notifyListeners();
        return true;
      } catch (networkError) {
        // RNF: Sección 5.4 - Prohibición de borrado y revertir a 'pendiente'
        for (var op in pendientes) {
          await _database.actualizarEstadoOperacion(op['id'].toString(), 'pendiente');
        }
        _loading = false;
        _error = 'Corte de red durante transmisión. Se preservaron las operaciones en cola: $networkError';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _loading = false;
      _error = 'Error en el proceso de sincronización: $e';
      notifyListeners();
      return false;
    }
  }
}

