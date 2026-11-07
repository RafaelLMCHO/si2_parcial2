import 'package:flutter/foundation.dart';
import '../core/session/session_controller.dart';

/// CU-04: Verificación de Correo y Activación
class CU04VerificacionEmailController extends ChangeNotifier {
  final SessionController _session;
  bool _loading = false;
  String? _error;
  String? _message;

  CU04VerificacionEmailController(this._session);

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
      final success = await _session.verifyEmail(
        empresaSlug: empresaSlug,
        token: token,
      );
      _loading = false;
      if (success) {
        _message = '¡Cuenta verificada exitosamente!';
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
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final success = await _session.resendVerification(
        empresaSlug: empresaSlug,
        correo: correo,
      );
      _loading = false;
      if (success) {
        _message = 'Enlace reenviado correctamente.';
      } else {
        _error = _session.error ?? 'No se pudo reenviar el correo';
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
}

