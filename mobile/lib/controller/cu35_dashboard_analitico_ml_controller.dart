import 'package:flutter/foundation.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/session/session_controller.dart';

class CU35DashboardAnaliticoMlController extends ChangeNotifier {
  final ApiClient apiClient;

  CU35DashboardAnaliticoMlController({required this.apiClient});

  factory CU35DashboardAnaliticoMlController.fromSession(SessionController session) {
    return CU35DashboardAnaliticoMlController(apiClient: session.apiClient);
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _error;
  String? get error => _error;

  Map<String, dynamic>? _dashboardMl;
  Map<String, dynamic>? get dashboardMl => _dashboardMl;

  Future<Map<String, dynamic>?> consultarDashboardMl() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await apiClient.get('/inteligencia/ml/dashboard');
      _dashboardMl = Map<String, dynamic>.from(res as Map);
      _isLoading = false;
      notifyListeners();
      return _dashboardMl;
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo cargar el dashboard ML.',
      ).message;
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> predecirDemanda() async {
    try {
      final res = await apiClient.get('/inteligencia/ml/demanda');
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo predecir la demanda.',
      ).message;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> segmentarClientes() async {
    try {
      final res = await apiClient.get('/inteligencia/ml/segmentacion');
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo segmentar clientes.',
      ).message;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> solicitarAudioTts(String texto) async {
    try {
      final res = await apiClient.post(
        '/inteligencia/ml/sintesis-audio',
        {'texto': texto},
      );
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo generar el audio ejecutivo.',
      ).message;
      notifyListeners();
      return null;
    }
  }
}

