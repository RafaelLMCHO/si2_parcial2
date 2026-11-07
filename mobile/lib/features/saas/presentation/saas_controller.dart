import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-06, CU-07, CU-08, CU-09: Onboarding SaaS, Empresas y Planes.
class SaasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _empresas = [];

  SaasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get empresas => _empresas;

  Future<void> cargarEmpresas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/saas/empresas');
      _empresas = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearEmpresa(Map<String, dynamic> payload) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/saas/empresas', payload);
      _loading = false;
      await cargarEmpresas();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

