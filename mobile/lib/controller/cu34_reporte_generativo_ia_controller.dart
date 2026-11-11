import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/session/session_controller.dart';

class CU34ReporteGenerativoIaController extends ChangeNotifier {
  final ApiClient apiClient;

  CU34ReporteGenerativoIaController({required this.apiClient});

  factory CU34ReporteGenerativoIaController.fromSession(
    SessionController session,
  ) {
    return CU34ReporteGenerativoIaController(apiClient: session.apiClient);
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  bool _exporting = false;
  bool get exporting => _exporting;

  String? _error;
  String? get error => _error;

  String _lastCanal = 'texto';
  String get lastCanal => _lastCanal;

  String? _lastPrompt;
  String? get lastPrompt => _lastPrompt;

  Map<String, dynamic>? _reporte;
  Map<String, dynamic>? get reporte => _reporte;

  void clearError() {
    if (_error != null) {
      _error = null;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>?> solicitarReporteIa({
    required String prompt,
    String canal = 'texto',
    String? audioBase64,
  }) async {
    final cleanedPrompt = prompt.trim();
    if (cleanedPrompt.length < 2) {
      _error = 'Ingrese o dicte una consulta de al menos 2 caracteres.';
      notifyListeners();
      return null;
    }

    _isLoading = true;
    _error = null;
    _lastCanal = canal;
    _lastPrompt = cleanedPrompt;
    notifyListeners();

    try {
      final res = await apiClient.post('/reportes/ia/consultar', {
        'prompt': cleanedPrompt,
        'canal': canal,
        'audio_base64': ?audioBase64,
      });
      if (res is! Map) {
        throw ApiException('Respuesta inesperada del servicio de reportes IA.');
      }
      _reporte = Map<String, dynamic>.from(res);
      _isLoading = false;
      notifyListeners();
      return _reporte;
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo generar el reporte IA.',
      ).message;
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> exportarReporte({
    String? consultaId,
    required String tipoReporte,
    required String formato,
    required String titulo,
    String? resumen,
    required List<String> columnas,
    required List<Map<String, dynamic>> filas,
  }) async {
    _exporting = true;
    _error = null;
    notifyListeners();

    try {
      final res = await apiClient.post('/reportes/ia/exportar', {
        'consulta_id': ?consultaId,
        'tipo_reporte': tipoReporte,
        'formato': formato,
        'titulo': titulo,
        'resumen': resumen,
        'columnas': columnas,
        'filas': filas,
      });
      _exporting = false;
      notifyListeners();
      if (res is Map) {
        return Map<String, dynamic>.from(res);
      }
      return null;
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo exportar el reporte.',
      ).message;
      _exporting = false;
      notifyListeners();
      return null;
    }
  }
}
