import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../utils/error_mapper.dart';

class ApiClient {
  ApiClient({String? baseUrl}) {
    dio = Dio(
      BaseOptions(
        baseUrl: baseUrl ?? AppConfig.apiBaseUrl,
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        headers: {'Accept': 'application/json'},
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = tokenProvider?.call();
          if (token != null && token.isNotEmpty && !_isAuthPath(options.path)) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final path = error.requestOptions.path;
          if (isNetworkError(error)) {
            networkLostHandler?.call();
            handler.next(error);
            return;
          }

          final status = error.response?.statusCode;
          final retried = error.requestOptions.extra['retried'] == true;
          if (status == 401 && !_isAuthPath(path) && !retried) {
            final refreshed = await _refreshOnce();
            if (refreshed) {
              final options = error.requestOptions;
              options.extra['retried'] = true;
              final token = tokenProvider?.call();
              if (token != null && token.isNotEmpty) {
                options.headers['Authorization'] = 'Bearer $token';
              }
              try {
                final response = await dio.fetch(options);
                handler.resolve(response);
                return;
              } on DioException catch (retryError) {
                handler.next(retryError);
                return;
              }
            }

            await sessionExpiredHandler?.call();
          }

          handler.next(error);
        },
      ),
    );
  }

  late final Dio dio;

  String? Function()? tokenProvider;
  Future<bool> Function()? refreshHandler;
  Future<void> Function()? sessionExpiredHandler;
  void Function()? networkLostHandler;

  Future<bool>? _refreshFuture;

  bool _isAuthPath(String path) {
    return path.contains('/auth/login') ||
        path.contains('/auth/register') ||
        path.contains('/auth/refresh') ||
        path.contains('/auth/verify-email');
  }

  Future<bool> _refreshOnce() {
    final existing = _refreshFuture;
    if (existing != null) {
      return existing;
    }

    final refresh = refreshHandler;
    if (refresh == null) {
      return Future.value(false);
    }

    final future = refresh().catchError((_) => false).whenComplete(() {
      _refreshFuture = null;
    });
    _refreshFuture = future;
    return future;
  }
}
