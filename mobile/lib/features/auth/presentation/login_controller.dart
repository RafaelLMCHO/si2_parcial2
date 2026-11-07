import 'package:flutter/foundation.dart';
import '../../../../core/session/session_controller.dart';

/// Controlador para CU-02: Inicio de Sesión Multi-inquilino
class LoginController extends ChangeNotifier {
  final SessionController _session;
  bool _loading = false;
  String? _error;

  LoginController(this._session);

  bool get loading => _loading;
  String? get error => _error;

  Future<bool> login({
    required String empresaSlug,
    required String correo,
    required String password,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final success = await _session.login(
        empresaSlug: empresaSlug,
        correo: correo,
        password: password,
      );
      _loading = false;
      if (!success) {
        _error = _session.error ?? 'Credenciales inválidas o empresa no encontrada';
      }
      notifyListeners();
      return success;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

