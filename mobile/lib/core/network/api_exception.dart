import 'package:dio/dio.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.code, this.statusCode});

  final String message;
  final String? code;
  final int? statusCode;

  factory ApiException.fromDio(DioException error, {String? fallback}) {
    final response = error.response;
    final data = response?.data;

    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is Map<String, dynamic>) {
        final message = detail['message']?.toString();
        final code = detail['code']?.toString();
        if (message != null && message.isNotEmpty) {
          return ApiException(
            message,
            code: code,
            statusCode: response?.statusCode,
          );
        }
      }
      final message = data['message']?.toString();
      if (message != null && message.isNotEmpty) {
        return ApiException(message, statusCode: response?.statusCode);
      }
    }

    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.unknown) {
      return ApiException(
        'Sin conexion. Revise su red e intente nuevamente.',
        code: 'RED_NO_DISPONIBLE',
        statusCode: response?.statusCode,
      );
    }

    switch (response?.statusCode) {
      case 401:
        return ApiException(
          'La sesion expiro. Inicie sesion nuevamente.',
          statusCode: 401,
        );
      case 402:
        return ApiException(
          'La empresa no tiene una suscripcion activa.',
          code: 'SUSCRIPCION_INACTIVA',
          statusCode: 402,
        );
      case 403:
        return ApiException(
          'La cuenta no esta habilitada para esta operacion.',
          statusCode: 403,
        );
      case 429:
        return ApiException(
          'Demasiados intentos. Espere unos minutos e intente nuevamente.',
          statusCode: 429,
        );
    }

    return ApiException(fallback ?? 'No se pudo completar la operacion.');
  }

  factory ApiException.fromObject(Object error, {String? fallback}) {
    if (error is ApiException) {
      return error;
    }
    if (error is DioException) {
      return ApiException.fromDio(error, fallback: fallback);
    }
    return ApiException(fallback ?? 'No se pudo completar la operacion.');
  }

  @override
  String toString() => message;
}
