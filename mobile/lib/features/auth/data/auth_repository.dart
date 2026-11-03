import 'package:dio/dio.dart';

import 'auth_models.dart';

class AuthRepository {
  AuthRepository(this._dio);

  final Dio _dio;

  Future<LoginResponse> login({
    required String empresaSlug,
    required String correo,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {
        'empresa_slug': empresaSlug.trim().isEmpty ? null : empresaSlug.trim(),
        'correo': correo.trim(),
        'password': password,
      },
    );
    return LoginResponse.fromJson(response.data!);
  }

  Future<RegisterResponse> register({
    required String empresaSlug,
    required String nombre,
    required String correo,
    String? telefono,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/register',
      data: {
        'empresa_slug': empresaSlug.trim(),
        'nombre': nombre.trim(),
        'correo': correo.trim(),
        'telefono': telefono?.trim().isEmpty == true ? null : telefono?.trim(),
        'password': password,
      },
    );
    return RegisterResponse.fromJson(response.data!);
  }

  Future<VerifyEmailResponse> verifyEmail({
    required String empresaSlug,
    required String token,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/verify-email',
      data: {'empresa_slug': empresaSlug.trim(), 'token': token.trim()},
    );
    return VerifyEmailResponse.fromJson(response.data!);
  }

  Future<RefreshResponse> refresh(String refreshToken) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return RefreshResponse.fromJson(response.data!);
  }

  Future<void> logout() async {
    await _dio.post<void>('/auth/logout');
  }
}
