import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../data/catalogo_models.dart';

/// Controlador para CU-14: Detalle de Producto, Variantes y Selección de Talla/Color
class DetalleProductoController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  Prenda? _prenda;
  VariantePrenda? _varianteSeleccionada;
  bool _esFavorito = false;

  DetalleProductoController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  Prenda? get prenda => _prenda;
  VariantePrenda? get varianteSeleccionada => _varianteSeleccionada;
  bool get esFavorito => _esFavorito;

  Future<void> cargarDetalle(String prendaId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/catalogo/prendas/$prendaId');
      _prenda = Prenda.fromJson(res);
      if (_prenda != null && _prenda!.variantes.isNotEmpty) {
        _varianteSeleccionada = _prenda!.variantes.first;
      }
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  void seleccionarVariante(VariantePrenda v) {
    _varianteSeleccionada = v;
    notifyListeners();
  }

  void toggleFavorito() {
    _esFavorito = !_esFavorito;
    notifyListeners();
  }
}

