import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-21: Validación, Preparación y Entrega de Reservas (Staff de Tienda)
class ReservaStaffController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _reservasSucursal = [];

  ReservaStaffController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get reservasSucursal => _reservasSucursal;

  Future<void> cargarReservasPorSucursal(String sucursalId, {String? estado}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final query = <String, String>{'sucursal_id': sucursalId};
      if (estado != null) query['estado'] = estado;
      final res = await _apiClient.get('/reservas', query: query);
      _reservasSucursal = (res['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<bool> prepararReserva(String reservaId, String sucursalId) async {
    return _ejecutarAccion('/reservas/$reservaId/preparar', sucursalId);
  }

  Future<bool> marcarCompletada(String reservaId, String sucursalId) async {
    return _ejecutarAccion('/reservas/$reservaId/completar', sucursalId);
  }

  Future<bool> registrarIncidencia(String reservaId, String sucursalId, String detalle) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/incidencia', {'detalle': detalle});
      await cargarReservasPorSucursal(sucursalId);
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> _ejecutarAccion(String endpoint, String sucursalId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post(endpoint, {});
      await cargarReservasPorSucursal(sucursalId);
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}

