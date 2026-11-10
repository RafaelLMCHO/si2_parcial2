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
  List<dynamic> get logs => _eventos;

  Future<void> cargarLogs() => cargarAuditoria();

  Future<void> cargarAuditoria() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/auditoria/logs');
      _eventos = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

