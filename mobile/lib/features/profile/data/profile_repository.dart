import 'package:dio/dio.dart';

import '../../auth/data/auth_models.dart';

class ProfileRepository {
  ProfileRepository(this._dio);

  final Dio _dio;

  Future<AppUser> me() async {
    final response = await _dio.get<Map<String, dynamic>>('/users/me');
    return AppUser.fromJson(response.data!);
  }

  Future<AppUser> updateMe({String? nombre, String? telefono}) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/users/me',
      data: {
        if (nombre != null) 'nombre': nombre,
        if (telefono != null) 'telefono': telefono,
      },
    );
    return AppUser.fromJson(response.data!);
  }

  Future<String> changePassword({
    required String passwordActual,
    required String passwordNueva,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/users/me/password',
      data: {
        'password_actual': passwordActual,
        'password_nueva': passwordNueva,
      },
    );
    return response.data?['mensaje']?.toString() ?? 'Contrasena actualizada.';
  }
}
