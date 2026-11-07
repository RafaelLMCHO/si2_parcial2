import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-09: Métricas SaaS / Superadmin Dashboard
class CU09MetricasSaasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  Map<String, dynamic> _metricas = {};

  CU09MetricasSaasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic> get metricas => _metricas;

  Future<void> cargarMetricas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/saas/metricas');
      _metricas = res;
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

