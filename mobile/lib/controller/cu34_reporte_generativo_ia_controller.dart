import 'package:flutter/foundation.dart';
import '../../core/network/api_client.dart';
import '../../core/session/session_controller.dart';

class CU34ReporteGenerativoIaController extends ChangeNotifier {
  final ApiClient apiClient;

  CU34ReporteGenerativoIaController({required this.apiClient});

  factory CU34ReporteGenerativoIaController.fromSession(SessionController session) {
    return CU34ReporteGenerativoIaController(apiClient: session.apiClient);
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _error;
  String? get error => _error;

  Map<String, dynamic>? _reporte;
  Map<String, dynamic>? get reporte => _reporte;

  Future<Map<String, dynamic>?> solicitarReporteIa({
    required String prompt,
    String canal = 'texto',
    String? audioBase64,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await apiClient.post(
        '/reportes/ia/consultar',
        {
          'prompt': prompt,
          'canal': canal,
          'audio_base64': ?audioBase64,
        },
      );
      _reporte = Map<String, dynamic>.from(res as Map);
      _isLoading = false;
      notifyListeners();
      return _reporte;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> exportarReporte({
    required String tipoReporte,
    required String formato,
    required String titulo,
    String? resumen,
    required List<String> columnas,
    required List<Map<String, dynamic>> filas,
  }) async {
    try {
      final res = await apiClient.post(
        '/reportes/ia/exportar',
        {
          'tipo_reporte': tipoReporte,
          'formato': formato,
          'titulo': titulo,
          'resumen': resumen,
          'columnas': columnas,
          'filas': filas,
        },
      );
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }
}

