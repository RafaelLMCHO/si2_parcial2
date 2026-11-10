import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-21: Preparación y Validación de Reservas en Tienda (Staff)
class CU21PreparacionReservasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _reservasSucursal = [];

  CU21PreparacionReservasController(this._apiClient);

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
    return _ejecutar('/reservas/$reservaId/preparar', sucursalId);
  }

  Future<bool> completarReserva(String reservaId, String sucursalId) async {
    return _ejecutar('/reservas/$reservaId/completar', sucursalId);
  }

  Future<bool> registrarIncidencia(
    String reservaId,
    String sucursalId,
    String detalle, {
    List<String> varianteIds = const [],
    bool registrarMerma = false,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/reservas/$reservaId/incidencia', {
        'variante_ids': varianteIds,
        'motivo': detalle,
        'registrar_merma': registrarMerma,
      });
      await cargarReservasPorSucursal(sucursalId);
      return true;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> _ejecutar(String endpoint, String sucursalId) async {
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

