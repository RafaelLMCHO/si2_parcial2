import 'package:flutter/foundation.dart';
import '../../../../core/session/session_controller.dart';

/// Controlador para CU-04: Verificación de Correo y Activación
class VerifyEmailController extends ChangeNotifier {
  final SessionController _session;
  bool _loading = false;
  String? _error;
  String? _message;

  VerifyEmailController(this._session);

  bool get loading => _loading;
  String? get error => _error;
  String? get message => _message;

  Future<bool> verificarToken({
    required String empresaSlug,
    required String token,
  }) async {
    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      final res = await _session.verifyEmail(
        empresaSlug: empresaSlug,
        token: token,
      );
      final success = res != null;
      _loading = false;
      if (success) {
        _message = '¡Cuenta verificada exitosamente! Ya puedes iniciar sesión.';
      } else {
        _error = _session.error ?? 'Token de verificación inválido o expirado';
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

  Future<bool> reenviarToken({
    required String empresaSlug,
    required String correo,
  }) async {
    _loading = false;
    _message = null;
    _error =
        'Utiliza el token generado en el registro de $correo ($empresaSlug) o solicita apoyo al administrador.';
    notifyListeners();
    return false;
  }
}

