import 'package:dio/dio.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.code, this.statusCode});

  final String message;
  final String? code;
  final int? statusCode;

  factory ApiException.fromDio(DioException error, {String? fallback}) {
    final response = error.response;
    final data = response?.data;

    if (data is Map) {
      final map = Map<String, dynamic>.from(data);
      final detail = map['detail'];
      if (detail is Map) {
        final detailMap = Map<String, dynamic>.from(detail);
        final message = detailMap['message']?.toString().trim();
        final code = detailMap['code']?.toString();
        if (message != null && message.isNotEmpty) {
          return ApiException(
            message,
            code: code,
            statusCode: response?.statusCode,
          );
        }
      } else if (detail is String && detail.trim().isNotEmpty) {
        return ApiException(
          detail.trim(),
          statusCode: response?.statusCode,
        );
      } else if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map && first['msg'] != null) {
          return ApiException(
            first['msg'].toString(),
            code: 'VALIDACION',
            statusCode: response?.statusCode,
          );
        }
        return ApiException(
          first.toString(),
          code: 'VALIDACION',
          statusCode: response?.statusCode,
        );
      }

      final message = map['message']?.toString().trim();
      if (message != null && message.isNotEmpty) {
        return ApiException(message, statusCode: response?.statusCode);
      }
    } else if (data is String &&
        data.trim().isNotEmpty &&
        !data.trimLeft().startsWith('<')) {
      return ApiException(
        data.trim(),
        statusCode: response?.statusCode,
      );
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
