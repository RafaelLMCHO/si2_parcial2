import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';
import '../core/network/api_exception.dart';
import '../core/utils/uuid_helper.dart';

/// CU-19: Creación de Reservas y Probador
class CU19CreacionReservasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;

  CU19CreacionReservasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;

  Future<Map<String, dynamic>?> crearReserva({
    required String sucursalId,
    required DateTime fechaVisita,
    required bool probador,
    required List<Map<String, dynamic>> items,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.post(
        '/reservas',
        {
          'sucursal_id': sucursalId,
          'fecha_visita': fechaVisita.toUtc().toIso8601String(),
          'probador': probador,
          'items': items,
        },
        {'Idempotency-Key': generateUuidV4()},
      );
      _loading = false;
      notifyListeners();
      return res is Map ? Map<String, dynamic>.from(res) : null;
    } catch (e) {
      _loading = false;
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo registrar la reserva.',
      ).message;
      notifyListeners();
      return null;
    }
  }
}

