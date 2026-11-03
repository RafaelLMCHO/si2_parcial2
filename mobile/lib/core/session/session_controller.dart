import 'package:flutter/foundation.dart';

import '../../features/auth/data/auth_models.dart';
import '../../features/auth/data/auth_repository.dart';
import '../../features/profile/data/profile_repository.dart';
import '../network/api_exception.dart';
import '../storage/local_database.dart';
import '../storage/secure_session_store.dart';
import '../utils/error_mapper.dart';
import '../utils/network_status.dart';

class SessionController extends ChangeNotifier {
  SessionController({
    required AuthRepository authRepository,
    required ProfileRepository profileRepository,
    required SecureSessionStore secureStore,
    required LocalDatabase database,
    required NetworkStatus networkStatus,
  }) : _authRepository = authRepository,
       _profileRepository = profileRepository,
       _secureStore = secureStore,
       _database = database,
       _networkStatus = networkStatus,
       _online = networkStatus.value {
    _networkStatus.addListener(_onNetworkChanged);
  }

  final AuthRepository _authRepository;
  final ProfileRepository _profileRepository;
  final SecureSessionStore _secureStore;
  final LocalDatabase _database;
  final NetworkStatus _networkStatus;

  String? _accessToken;
  String? _refreshToken;
  DateTime? _expiresAt;
  AppUser? _user;
  String _tenant = 'demo';
  int _pendingOperations = 0;
  DateTime? _lastSync;
  bool _online;
  bool _loading = false;
  bool _bootstrapping = true;
  String? _error;
  String? _message;
  String? _notice;

  String? get accessToken => _accessToken;
  AppUser? get user => _user;
  String get tenant => _tenant;
  int get pendingOperations => _pendingOperations;
  DateTime? get lastSync => _lastSync;
  bool get isOnline => _online;
  bool get loading => _loading;
  bool get isBootstrapping => _bootstrapping;
  String? get error => _error;
  String? get message => _message;
  String? get notice => _notice;

  bool get isAuthenticated => _accessToken != null && _user != null;

  bool get isSessionExpired {
    final expiresAt = _expiresAt;
    return expiresAt != null && DateTime.now().isAfter(expiresAt);
  }

  bool get canWrite => isAuthenticated && _online && !isSessionExpired;

  Future<void> bootstrap() async {
    _accessToken = await _secureStore.readAccessToken();
    _refreshToken = await _secureStore.readRefreshToken();
    _expiresAt = await _secureStore.readExpiresAt();
    _user = await _database.readUser();
    _tenant = await _database.readTenant() ?? 'demo';
    _pendingOperations = await _database.pendingOperationsCount();
    _lastSync = await _database.readLastSync();
    _online = _networkStatus.value;
    _bootstrapping = false;

    if (_accessToken != null && _user == null && _online) {
      await refreshProfile();
    }

    if (isAuthenticated && isSessionExpired) {
      if (_online && _refreshToken != null) {
        final refreshed = await refreshTokens();
        if (!refreshed && _error == null) {
          await handleSessionExpired();
        }
      } else {
        _notice = 'La sesion local expiro. Reconectese para renovarla.';
      }
    } else if (isAuthenticated && _online) {
      await refreshProfile();
    }

    notifyListeners();
  }

  Future<bool> login({
    required String empresaSlug,
    required String correo,
    required String password,
  }) async {
    _loading = true;
    _error = null;
    _message = null;
    _notice = null;
    notifyListeners();

    try {
      final response = await _authRepository.login(
        empresaSlug: empresaSlug,
        correo: correo,
        password: password,
      );
      await _applyLogin(response, tenantSlug: empresaSlug.trim());
      _message = 'Sesion iniciada correctamente.';
      return true;
    } catch (error) {
      _setOperationError(error, fallback: 'No se pudo iniciar sesion.');
      return false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<RegisterResponse?> register({
    required String empresaSlug,
    required String nombre,
    required String correo,
    String? telefono,
    required String password,
  }) async {
    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      final response = await _authRepository.register(
        empresaSlug: empresaSlug,
        nombre: nombre,
        correo: correo,
        telefono: telefono,
        password: password,
      );
      _tenant = empresaSlug.trim();
      await _database.saveTenant(_tenant);
      return response;
    } catch (error) {
      _setOperationError(error, fallback: 'No se pudo completar el registro.');
      return null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<VerifyEmailResponse?> verifyEmail({
    required String empresaSlug,
    required String token,
  }) async {
    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      final response = await _authRepository.verifyEmail(
        empresaSlug: empresaSlug,
        token: token,
      );
      _tenant = empresaSlug.trim();
      await _database.saveTenant(_tenant);
      _message = response.mensaje;
      return response;
    } catch (error) {
      _setOperationError(error, fallback: 'No se pudo verificar el correo.');
      return null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<bool> refreshTokens() async {
    final refreshToken = _refreshToken;
    if (refreshToken == null) {
      return false;
    }

    try {
      final response = await _authRepository.refresh(refreshToken);
      final expiresAt = DateTime.now().add(
        Duration(seconds: response.expiresIn),
      );
      _accessToken = response.accessToken;
      _refreshToken = response.refreshToken;
      _expiresAt = expiresAt;
      await _secureStore.saveTokens(
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
        expiresAt: expiresAt,
      );
      _networkStatus.markOnline();
      notifyListeners();
      return true;
    } catch (error) {
      final apiError = ApiException.fromObject(error);
      if (apiError.statusCode == 401) {
        await _clearAuth();
        _notice = 'La sesion expiro. Inicie sesion nuevamente.';
      } else if (isNetworkError(error)) {
        _networkStatus.markOffline();
        _notice = 'Sin conexion. Se conserva la sesion local.';
      } else {
        _error = apiError.message;
      }
      notifyListeners();
      return false;
    }
  }

  Future<void> refreshProfile() async {
    if (_accessToken == null) {
      return;
    }
    if (!_online) {
      _notice =
          'Sin conexion. Se muestran los datos guardados en este dispositivo.';
      notifyListeners();
      return;
    }

    try {
      final user = await _profileRepository.me();
      _user = user;
      _lastSync = DateTime.now();
      _error = null;
      await _database.saveUser(user);
      await _database.saveLastSync(_lastSync!);
      notifyListeners();
    } catch (error) {
      final apiError = ApiException.fromObject(
        error,
        fallback: 'No se pudo cargar el perfil.',
      );
      if (isNetworkError(error)) {
        _networkStatus.markOffline();
        _notice = 'No se pudo contactar al servidor. Se muestran los datos guardados.';
      } else {
        _error = apiError.message;
      }
      notifyListeners();
    }
  }

  Future<bool> updateProfile({
    required String nombre,
    required String? telefono,
  }) async {
    if (!canWrite) {
      _error =
          'No puede guardar cambios sin conexion o con la sesion expirada.';
      notifyListeners();
      return false;
    }

    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      final user = await _profileRepository.updateMe(
        nombre: nombre,
        telefono: telefono,
      );
      _user = user;
      _lastSync = DateTime.now();
      await _database.saveUser(user);
      await _database.saveLastSync(_lastSync!);
      _message = 'Perfil actualizado correctamente.';
      return true;
    } catch (error) {
      _setOperationError(error, fallback: 'No se pudo actualizar el perfil.');
      return false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<bool> changePassword({
    required String passwordActual,
    required String passwordNueva,
  }) async {
    if (!canWrite) {
      _error = 'No puede cambiar la contrasena sin conexion o con la sesion expirada.';
      notifyListeners();
      return false;
    }

    _loading = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      _message = await _profileRepository.changePassword(
        passwordActual: passwordActual,
        passwordNueva: passwordNueva,
      );
      return true;
    } catch (error) {
      _setOperationError(error, fallback: 'No se pudo cambiar la contrasena.');
      return false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    try {
      if (_online && _accessToken != null) {
        await _authRepository.logout();
      }
    } catch (_) {
      // El cierre local debe completarse aunque el servidor no responda.
    } finally {
      await _clearAuth();
      _message = null;
      _error = null;
      _notice = _online ? null : 'Sesion cerrada en este dispositivo. Las operaciones pendientes se conservaron.';
      notifyListeners();
    }
  }

  Future<void> handleSessionExpired() async {
    await _clearAuth();
    _notice = 'La sesion expiro. Inicie sesion nuevamente.';
    notifyListeners();
  }

  void handleNetworkLost() {
    _networkStatus.markOffline();
  }

  Future<void> saveTenant(String slug) async {
    _tenant = slug.trim().isEmpty ? 'demo' : slug.trim();
    await _database.saveTenant(_tenant);
    notifyListeners();
  }

  void clearMessages() {
    _error = null;
    _message = null;
    _notice = null;
    notifyListeners();
  }

  Future<void> _applyLogin(
    LoginResponse response, {
    required String tenantSlug,
  }) async {
    final expiresAt = DateTime.now().add(Duration(seconds: response.expiresIn));
    _accessToken = response.accessToken;
    _refreshToken = response.refreshToken;
    _expiresAt = expiresAt;
    _user = response.usuario;
    _tenant = tenantSlug.isEmpty ? 'demo' : tenantSlug;
    _lastSync = DateTime.now();
    _pendingOperations = await _database.pendingOperationsCount();

    await _secureStore.saveTokens(
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      expiresAt: expiresAt,
    );
    await _database.saveUser(response.usuario);
    await _database.saveTenant(_tenant);
    await _database.saveLastSync(_lastSync!);
    _networkStatus.markOnline();
  }

  Future<void> _clearAuth() async {
    await _secureStore.clear();
    await _database.clearUserCache();
    _accessToken = null;
    _refreshToken = null;
    _expiresAt = null;
    _user = null;
    _lastSync = null;
    _pendingOperations = await _database.pendingOperationsCount();
  }

  void _setOperationError(Object error, {required String fallback}) {
    final apiError = ApiException.fromObject(error, fallback: fallback);
    if (isNetworkError(error)) {
      _networkStatus.markOffline();
    }
    _error = apiError.message;
  }

  void _onNetworkChanged() {
    _online = _networkStatus.value;
    if (!_online) {
      _notice = 'Sin conexion. Las escrituras estan deshabilitadas.';
    } else if (_notice != null) {
      _notice = null;
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _networkStatus.removeListener(_onNetworkChanged);
    super.dispose();
  }
}
