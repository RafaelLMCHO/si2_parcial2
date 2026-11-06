import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-15: Administrar Proveedores Textiles.
class ProveedoresController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _proveedores = [];

  ProveedoresController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get proveedores => _proveedores;

  Future<void> cargarProveedores() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/proveedores');
      _proveedores = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearProveedor(Map<String, dynamic> payload) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/proveedores', payload);
      _loading = false;
      await cargarProveedores();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

