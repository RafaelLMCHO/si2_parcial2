import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';

/// Controlador para CU-11: Administrar Sucursales y Límite por Plan.
class SucursalesController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _sucursales = [];
  int? _limitePlan;
  int _total = 0;
  int _activas = 0;

  SucursalesController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get sucursales => _sucursales;
  int? get limitePlan => _limitePlan;
  int get total => _total;
  int get activas => _activas;

  Future<void> cargarSucursales() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/sucursales');
      if (res is List) {
        _sucursales = res;
        _total = res.length;
        _activas = res
            .where((s) => s is Map && (s['estado'] == 'activa' || s['activo'] == true))
            .length;
        _limitePlan = null;
      } else if (res is Map) {
        final map = Map<String, dynamic>.from(res);
        _sucursales = (map['items'] as List<dynamic>? ?? []);
        _limitePlan = (map['limite_plan'] as num?)?.toInt();
        _total = (map['total'] as num?)?.toInt() ?? _sucursales.length;
        _activas = (map['activas'] as num?)?.toInt() ??
            _sucursales
                .where(
                  (s) => s is Map && (s['estado'] == 'activa' || s['activo'] == true),
                )
                .length;
      } else {
        _sucursales = [];
        _limitePlan = null;
        _total = 0;
        _activas = 0;
      }
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudieron cargar las sucursales.',
      ).message;
    }
    notifyListeners();
  }

  Future<bool> crearSucursal(Map<String, dynamic> payload) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiClient.post('/sucursales', payload);
      _loading = false;
      await cargarSucursales();
      return true;
    } catch (e) {
      _loading = false;
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo crear la sucursal.',
      ).message;
      notifyListeners();
      return false;
    }
  }
}
