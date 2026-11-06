import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-11: Administrar Sucursales y Límite por Plan.
class SucursalesController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _sucursales = [];
  Map<String, dynamic>? _limitePlan;

  SucursalesController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get sucursales => _sucursales;
  Map<String, dynamic>? get limitePlan => _limitePlan;

  Future<void> cargarSucursales() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/sucursales');
      _sucursales = (res['items'] as List<dynamic>? ?? []);
      _limitePlan = res['limite_plan'];
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearSucursal(Map<String, dynamic> payload) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/sucursales', payload);
      _loading = false;
      await cargarSucursales();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

