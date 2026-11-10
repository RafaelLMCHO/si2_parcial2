import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-10: Gestión de Empleados, Usuarios y Roles
class CU10GestionEmpleadosController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _empleados = [];

  CU10GestionEmpleadosController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get empleados => _empleados;

  Future<void> cargarEmpleados() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/empleados');
      _empleados = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearEmpleado(Map<String, dynamic> data) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/empleados', data);
      await cargarEmpleados();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

