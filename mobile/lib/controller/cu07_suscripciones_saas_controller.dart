import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-07: Suscripciones SaaS y Pagos Stripe
class CU07SuscripcionesSaasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _suscripcionActual;

  CU07SuscripcionesSaasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic>? get suscripcionActual => _suscripcionActual;

  Future<void> cargarSuscripcionActual() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/saas/suscripcion/actual');
      _suscripcionActual = res;
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<Map<String, dynamic>?> suscribirse({required String planId, required String paymentMethodId}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.post('/saas/suscripcion', {
        'plan_id': planId,
        'payment_method_id': paymentMethodId,
      });
      await cargarSuscripcionActual();
      return res;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> cancelarSuscripcion() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/saas/suscripcion/cancelar', {});
      await cargarSuscripcionActual();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

