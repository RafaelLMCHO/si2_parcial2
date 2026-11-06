import 'package:flutter/foundation.dart';
import '../core/session/session_controller.dart';
import '../features/auth/data/auth_models.dart';

/// CU-01: Registro de Empresa / Onboarding de Inquilino
class CU01RegistroInquilinoController extends ChangeNotifier {
  final SessionController _session;
  bool _loading = false;
  String? _error;
  String? _successMessage;

  CU01RegistroInquilinoController(this._session);

  bool get loading => _loading;
  String? get error => _error;
  String? get successMessage => _successMessage;

  Future<RegisterResponse?> registrarEmpresa({
    required String tenantSlug,
    required String nombre,
    required String email,
    String? telefono,
    required String password,
  }) async {
    _loading = true;
    _error = null;
    _successMessage = null;
    notifyListeners();

    try {
      final res = await _session.register(
        empresaSlug: tenantSlug,
        nombre: nombre,
        correo: email,
        telefono: telefono,
        password: password,
      );
      _loading = false;
      _successMessage = 'Registro exitoso. Revisa tu correo para verificar tu cuenta.';
      notifyListeners();
      return res;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  void clearError() {
    _error = null;
    _successMessage = null;
    notifyListeners();
  }
}

