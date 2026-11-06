import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-20: Consulta y Gestión de Reservas del Cliente
class ReservaClienteController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _misReservas = [];

  ReservaClienteController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get misReservas => _misReservas;

  Future<void> cargarMisReservas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/reservas/mis-reservas');
      _misReservas = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> cancelarReserva(String reservaId, {String? motivo}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/cancelar', {
        if (motivo != null) 'motivo': motivo,
      });
      await cargarMisReservas();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

