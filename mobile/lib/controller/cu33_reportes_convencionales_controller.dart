import 'package:flutter/foundation.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/session/session_controller.dart';

class CU33ReportesConvencionalesController extends ChangeNotifier {
  final ApiClient apiClient;

  CU33ReportesConvencionalesController({required this.apiClient});

  factory CU33ReportesConvencionalesController.fromSession(SessionController session) {
    return CU33ReportesConvencionalesController(apiClient: session.apiClient);
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _error;
  String? get error => _error;

  Map<String, dynamic>? _dashboard;
  Map<String, dynamic>? get dashboard => _dashboard;

  Future<Map<String, dynamic>?> obtenerDashboard() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await apiClient.get('/reportes/convencionales/dashboard');
      _dashboard = Map<String, dynamic>.from(res as Map);
      _isLoading = false;
      notifyListeners();
      return _dashboard;
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudieron cargar los reportes convencionales.',
      ).message;
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> consultarVentasPeriodo({
    String? fechaInicio,
    String? fechaFin,
    String? sucursalId,
  }) async {
    try {
      final params = <String, dynamic>{};
      if (fechaInicio != null) params['fecha_inicio'] = fechaInicio;
      if (fechaFin != null) params['fecha_fin'] = fechaFin;
      if (sucursalId != null) params['sucursal_id'] = sucursalId;

      final res = await apiClient.get('/reportes/convencionales/ventas', queryParameters: params);
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo consultar ventas del período.',
      ).message;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> consultarRotacionStock() async {
    try {
      final res = await apiClient.get('/reportes/convencionales/rotacion');
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo consultar la rotación de stock.',
      ).message;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> consultarTopPrendas({int limite = 10}) async {
    try {
      final res = await apiClient.get(
        '/reportes/convencionales/top-prendas',
        queryParameters: {'limite': limite},
      );
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo consultar el top de prendas.',
      ).message;
      notifyListeners();
      return null;
    }
  }
}

