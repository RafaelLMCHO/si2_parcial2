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
      final res = await _apiClient.get('/mi-suscripcion');
      _suscripcionActual = Map<String, dynamic>.from(res as Map);
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
      final body = <String, dynamic>{
        'payment_method_id': paymentMethodId,
      };
      final parsedPlanId = int.tryParse(planId);
      if (parsedPlanId != null) {
        body['plan_id'] = parsedPlanId;
      } else {
        body['plan_codigo'] = planId;
      }

      final res = await _apiClient.put('/mi-suscripcion', body);
      _suscripcionActual = Map<String, dynamic>.from(res as Map);
      _loading = false;
      notifyListeners();
      return _suscripcionActual;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> cancelarSuscripcion({String? motivo}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.post('/mi-suscripcion/cancelar', {
        'motivo': motivo ?? 'Cancelacion solicitada desde app movil',
      });
      if (res is Map) {
        _suscripcionActual = Map<String, dynamic>.from(res);
      }
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

