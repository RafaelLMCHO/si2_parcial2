import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-15: Gestión de Proveedores
class CU15GestionProveedoresController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _proveedores = [];

  CU15GestionProveedoresController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get proveedores => _proveedores;

  Future<void> cargarProveedores() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/proveedores');
      _proveedores = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

