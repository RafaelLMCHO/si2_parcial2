import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-16: Administrar Temporadas y Colecciones Comerciales.
class TemporadasController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _colecciones = [];
  List<dynamic> _temporadas = [];

  TemporadasController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get colecciones => _colecciones;
  List<dynamic> get temporadas => _temporadas;

  Future<void> cargar() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final colRes = await _apiClient.get('/colecciones');
      _colecciones = (colRes['items'] as List<dynamic>? ?? []);

      final tempRes = await _apiClient.get('/colecciones/temporadas');
      _temporadas = (tempRes['items'] as List<dynamic>? ?? []);

      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

