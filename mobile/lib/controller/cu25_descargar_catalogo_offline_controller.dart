import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';
import '../core/storage/local_database.dart';

/// CU-25: Descargar catálogo offline (persistencia en SQLite / IndexedDB)
class CU25DescargarCatalogoOfflineController extends ChangeNotifier {
  final ApiClient _apiClient;
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  DateTime? _ultimaDescarga;
  int _articulosDescargados = 0;

  CU25DescargarCatalogoOfflineController(this._apiClient, this._database);

  bool get loading => _loading;
  String? get error => _error;
  DateTime? get ultimaDescarga => _ultimaDescarga;
  int get articulosDescargados => _articulosDescargados;

  Future<bool> descargarCatalogo({String? sucursalId}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final query = <String, String>{};
      if (sucursalId != null) query['sucursal_id'] = sucursalId;

      final res = await _apiClient.get('/sync/catalogo-offline', query: query);
      final prendas = (res['prendas'] as List<dynamic>? ?? []);
      final variantes = (res['variantes'] as List<dynamic>? ?? []);

      _articulosDescargados = variantes.length;
      _ultimaDescarga = DateTime.now();

      // Guardar meta fecha en local
      await _database.saveLastSync(_ultimaDescarga!);

      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Error al descargar catálogo offline: $e';
      notifyListeners();
      return false;
    }
  }
}

