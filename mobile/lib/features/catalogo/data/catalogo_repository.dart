import 'package:dio/dio.dart';

import 'catalogo_models.dart';

class CatalogoRepository {
  CatalogoRepository(this._dio);

  final Dio _dio;

  Future<PrendaListResponse> listarPrendas({
    required String empresaSlug,
    CatalogoFiltros filtros = const CatalogoFiltros(),
    int limit = 50,
    int offset = 0,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/catalogo/prendas',
      queryParameters: {
        ...filtros.toQueryParams(empresaSlug),
        'limit': limit,
        'offset': offset,
      },
    );
    return PrendaListResponse.fromJson(response.data ?? const {});
  }

  Future<AuxiliaresCatalogo> obtenerAuxiliares(String empresaSlug) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/catalogo/auxiliares',
      queryParameters: {'empresa_slug': empresaSlug},
    );
    return AuxiliaresCatalogo.fromJson(response.data ?? const {});
  }
}
