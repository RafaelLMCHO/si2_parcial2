import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

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
      final res = await _apiClient.post('/reservas', {
        'sucursal_id': sucursalId,
        'fecha_visita': fechaVisita.toIso8601String(),
        'probador': probador,
        'items': items,
      });
      _loading = false;
      notifyListeners();
      return res;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }
}

