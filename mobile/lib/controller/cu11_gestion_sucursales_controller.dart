import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-11: Gestión de Sucursales
class CU11GestionSucursalesController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _sucursales = [];

  CU11GestionSucursalesController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get sucursales => _sucursales;

  Future<void> cargarSucursales() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/sucursales');
      _sucursales = res is List ? res : (res['items'] ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

