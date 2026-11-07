import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-10: Usuarios y Roles por Empresa.
class EmpleadosController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _empleados = [];

  EmpleadosController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get empleados => _empleados;

  Future<void> cargarEmpleados() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/empleados');
      _empleados = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearEmpleado(Map<String, dynamic> payload) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/empleados', payload);
      _loading = false;
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

