import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-17: Gestionar inventario, ajustes y transferencias.
class InventarioController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _items = [];
  List<dynamic> _movimientos = [];

  InventarioController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get items => _items;
  List<dynamic> get movimientos => _movimientos;

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
      _loading = false;
      await cargarInventario();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> crearTransferencia(String origenId, String destinoId, List<Map<String, dynamic>> items) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/inventario/transferencias', {
        'origen_id': origenId,
        'destino_id': destinoId,
        'items': items,
      });
      _loading = false;
      await cargarInventario();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> cargarKardex() async {
    _loading = true;
    notifyListeners();
    try {
      final res = await _apiClient.get('/inventario/movimientos');
      _movimientos = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

