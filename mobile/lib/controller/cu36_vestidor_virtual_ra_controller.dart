import 'package:flutter/foundation.dart';
import '../../core/network/api_client.dart';
import '../../core/session/session_controller.dart';

class CU36VestidorVirtualRaController extends ChangeNotifier {
  final ApiClient apiClient;

  CU36VestidorVirtualRaController({required this.apiClient});

  factory CU36VestidorVirtualRaController.fromSession(SessionController session) {
    return CU36VestidorVirtualRaController(apiClient: session.apiClient);
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _error;
  String? get error => _error;

  List<Map<String, dynamic>> _prendasAr = [];
  List<Map<String, dynamic>> get prendasAr => _prendasAr;

  Future<List<Map<String, dynamic>>> listarPrendasAr() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await apiClient.get('/vestidor/prendas');
      _prendasAr = List<Map<String, dynamic>>.from(res.data);
      _isLoading = false;
      notifyListeners();
      return _prendasAr;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return [];
    }
  }

  Future<Map<String, dynamic>?> obtenerPrendaAr(String prendaId) async {
    try {
      final res = await apiClient.get('/vestidor/prendas/$prendaId');
      return Map<String, dynamic>.from(res.data);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> obtenerAvatarUsuario() async {
    try {
      final res = await apiClient.get('/vestidor/avatar');
      return Map<String, dynamic>.from(res.data);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> iniciarSesionPrueba({
    required String prendaId,
    String? varianteId,
    String? avatarId,
  }) async {
    try {
      final res = await apiClient.post(
        '/vestidor/sesiones',
        data: {
          'prenda_id': prendaId,
          if (varianteId != null) 'variante_id': varianteId,
          if (avatarId != null) 'avatar_id': avatarId,
        },
      );
      return Map<String, dynamic>.from(res.data);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> finalizarSesionPrueba(
    String sesionId, {
    String estado = 'completada',
    String? resultadoUrl,
  }) async {
    try {
      await apiClient.put(
        '/vestidor/sesiones/$sesionId',
        data: {
          'estado': estado,
          if (resultadoUrl != null) 'resultado_url': resultadoUrl,
        },
      );
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

