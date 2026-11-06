import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-24: Procesamiento de Pagos, Pasarelas y Reembolsos
class CU24ProcesamientoPagosController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _pagoActual;

  CU24ProcesamientoPagosController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic>? get pagoActual => _pagoActual;

  Future<Map<String, dynamic>?> crearIntencionPago({
    required String ventaId,
    String pasarela = 'stripe',
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.post('/pagos/intencion', {
        'venta_id': ventaId,
        'pasarela': pasarela,
      });
      _pagoActual = res;
      _loading = false;
      notifyListeners();
      return res;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> consultarEstadoPago(String pagoId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/pagos/$pagoId');
      _pagoActual = res;
      _loading = false;
      notifyListeners();
      return res;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> solicitarReembolso({
    required String pagoId,
    required String motivo,
    double? montoParcial,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/pagos/$pagoId/reembolsar', {
        'motivo': motivo,
        if (montoParcial != null) 'monto': montoParcial,
      });
      _loading = false;
      await consultarEstadoPago(pagoId);
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

