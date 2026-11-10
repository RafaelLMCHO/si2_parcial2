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

  Future<void> consultarDisponibilidad(String prendaId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/inventario/prendas/$prendaId/disponibilidad');
      if (res is Map) {
        _tiendas = (res['sucursales'] as List<dynamic>? ?? res['tiendas'] as List<dynamic>? ?? []);
      } else {
        _tiendas = [];
      }
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

