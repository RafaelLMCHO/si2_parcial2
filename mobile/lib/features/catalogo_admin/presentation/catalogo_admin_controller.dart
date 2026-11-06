import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-12: Catálogo de Prendas y Variantes (Administración).
class CatalogoAdminController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _prendas = [];

  CatalogoAdminController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get prendas => _prendas;

  Future<void> cargarPrendas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/catalogo/admin/prendas');
      _prendas = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearPrenda(Map<String, dynamic> payload) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/catalogo/admin/prendas', payload);
      _loading = false;
      await cargarPrendas();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

