import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-05: Bitácora de Auditoría y Trazabilidad.
class AuditoriaController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _eventos = [];

  AuditoriaController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get eventos => _eventos;

  Future<void> cargarAuditoria() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/saas/auditoria');
      _eventos = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

