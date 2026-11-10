import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-16: Gestión de Temporadas y Colecciones
class CU16GestionTemporadasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _temporadas = [];

  CU16GestionTemporadasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get temporadas => _temporadas;

  Future<void> cargarTemporadas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/temporadas-colecciones/temporadas');
      _temporadas = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

