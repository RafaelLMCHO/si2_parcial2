import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-06, CU-07, CU-08, CU-09: Onboarding SaaS, Empresas y Planes.
class SaasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _empresas = [];
  List<dynamic> _planes = [];
  Map<String, dynamic> _metricas = {};

  SaasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get empresas => _empresas;
  List<dynamic> get planes => _planes;
  Map<String, dynamic> get metricas => _metricas;

  Future<void> cargarEmpresas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/saas/empresas');
      _empresas = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<void> cargarPlanes() async {
    try {
      final dynamic res = await _apiClient.get('/saas/planes');
      _planes = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
    } catch (e) {
      _error ??= e.toString();
    }
    notifyListeners();
  }

  Future<void> cargarMetricas() async {
    try {
      final dynamic res = await _apiClient.get('/saas/metricas');
      if (res is Map) {
        _metricas = Map<String, dynamic>.from(res);
      }
    } catch (e) {
      _error ??= e.toString();
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

