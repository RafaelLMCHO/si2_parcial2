import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-17: Gestión de Inventario, Kardex, Ajustes y Alertas
class CU17GestionInventarioController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _items = [];

  CU17GestionInventarioController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get items => _items;

  Future<void> cargarInventario({String? q, bool soloBajoMinimo = false}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final query = <String, String>{};
      if (q != null && q.isNotEmpty) query['q'] = q;
      if (soloBajoMinimo) query['solo_bajo_minimo'] = 'true';

      final res = await _apiClient.get('/inventario', query: query);
      _items = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> registrarAjuste(String sucursalId, String varianteId, int cantidad, String motivo) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/inventario/movimientos/ajuste', {
        'sucursal_id': sucursalId,
        'variante_id': varianteId,
        'cantidad': cantidad,
        'motivo': motivo,
      });
      await cargarInventario();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

