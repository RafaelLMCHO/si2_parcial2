import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-19, CU-20, CU-21: Reservas, Cancelación y Preparación en Probadores.
class ReservasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  String? _message;
  List<dynamic> _reservas = [];

  ReservasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  String? get message => _message;
  List<dynamic> get reservas => _reservas;

  Future<void> cargarReservas({bool esEncargado = false}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final endpoint = esEncargado ? '/reservas/por-preparar' : '/reservas';
      final res = await _apiClient.get(endpoint);
      _reservas = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> crearReserva(Map<String, dynamic> payload, String idempotencyKey) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post(
        '/reservas',
        payload,
        headers: {'Idempotency-Key': idempotencyKey},
      );
      _loading = false;
      await cargarReservas();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> cancelarReserva(String reservaId, {String? motivo}) async {
    _loading = true;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/cancelar', {'motivo': motivo});
      _loading = false;
      await cargarReservas();
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> prepararReserva(String reservaId, String probador) async {
    _loading = true;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/preparar', {'probador': probador});
      _loading = false;
      await cargarReservas(esEncargado: true);
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

