import 'package:flutter/foundation.dart';
import '../core/session/session_controller.dart';
import '../features/profile/data/profile_repository.dart';

/// CU-03: Perfil de Usuario y Cambio de Contraseña
class CU03PerfilUsuarioController extends ChangeNotifier {
  final ProfileRepository _profileRepo;
  final SessionController _session;
  bool _loading = false;
  String? _error;
  String? _message;

  CU03PerfilUsuarioController(this._profileRepo, this._session);

  bool get loading => _loading;
  String? get error => _error;
  String? get message => _message;

  Future<bool> cambiarPassword({
    required String passwordActual,
    required String passwordNuevo,
  }) async {
    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      await _profileRepo.changePassword(
        passwordActual: passwordActual,
        passwordNueva: passwordNuevo,
      );
      _loading = false;
      _message = 'Contraseña actualizada con éxito.';
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> refrescarPerfil() async {
    await _session.refreshProfile();
  }
}

