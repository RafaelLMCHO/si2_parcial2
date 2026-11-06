import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-32: Resolver conflictos de sincronización con políticas y manual (FIFO)
class CU32ResolverConflictosController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _conflictos = [];

  CU32ResolverConflictosController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get conflictos => _conflictos;

  Future<void> cargarConflictos({String? sucursalId}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final query = <String, String>{};
      if (sucursalId != null) query['sucursal_id'] = sucursalId;

      final res = await _apiClient.get('/sync/conflictos', query: query);
      _conflictos = (res as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = 'Error cargando conflictos: $e';
    }
    notifyListeners();
  }

  Future<bool> resolverConflicto({
    required String operacionId,
    required String decision, // 'ajustar' | 'aceptar' | 'rechazar' | 'sustituir'
    String? motivo,
    Map<String, dynamic>? detalle,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/sync/conflictos/resolver', {
        'operacion_id': operacionId,
        'decision': decision,
        if (motivo != null) 'motivo': motivo,
        if (detalle != null) 'detalle': detalle,
      });

      await cargarConflictos();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Error al resolver conflicto: $e';
      notifyListeners();
      return false;
    }
  }
}

