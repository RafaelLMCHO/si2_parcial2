import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-05: Auditoría y Trazabilidad de Logs
class CU05AuditoriaLogsController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _logs = [];

  CU05AuditoriaLogsController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get logs => _logs;

  Future<void> cargarLogs({String? usuarioId, String? accion}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final query = <String, String>{};
      if (usuarioId != null) query['usuario_id'] = usuarioId;
      if (accion != null) query['accion'] = accion;

      final res = await _apiClient.get('/auditoria/logs', query: query);
      _logs = res is List ? res : (res['items'] ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

