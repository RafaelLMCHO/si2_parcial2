import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-18: Disponibilidad en Tiendas / Búsqueda Omnicanal
class CU18DisponibilidadTiendasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _tiendas = [];

  CU18DisponibilidadTiendasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get tiendas => _tiendas;

  Future<void> consultarDisponibilidad(String varianteId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/inventario/disponibilidad/variante/$varianteId');
      _tiendas = (res['tiendas'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

