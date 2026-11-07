import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../../auth/data/auth_models.dart';

/// Controlador para CU-03: Perfil de usuario y cambio de contraseña.
class ProfileController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  String? _message;
  AppUser? _user;

  ProfileController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  String? get message => _message;
  AppUser? get user => _user;

  Future<void> cargarPerfil() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/users/me');
      _user = AppUser.fromJson(res);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> cambiarPassword(String actual, String nueva) async {
    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      await _apiClient.post('/users/me/password', {
        'password_actual': actual,
        'password_nueva': nueva,
      });
      _message = 'Contraseña actualizada exitosamente';
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

