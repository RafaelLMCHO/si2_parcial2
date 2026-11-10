import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-06: Gestión de Planes SaaS (Superadmin)
class PlanesController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _planes = [];

  PlanesController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get planes => _planes;

  Future<void> cargarPlanes() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/saas/planes');
      _planes = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> guardarPlan(Map<String, dynamic> data, {String? planId}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      if (planId != null) {
        await _apiClient.put('/saas/planes/$planId', data);
      } else {
        await _apiClient.post('/saas/planes', data);
      }
      await cargarPlanes();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> eliminarPlan(String planId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.delete('/saas/planes/$planId');
      await cargarPlanes();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

