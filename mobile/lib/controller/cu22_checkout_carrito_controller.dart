import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-22: Carrito de Compras y Checkout Omnicanal
class CU22CheckoutCarritoController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _carrito;
  String _tipoEntrega = 'envio'; // 'envio' | 'retiro'
  String? _sucursalRetiroId;

  CU22CheckoutCarritoController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic>? get carrito => _carrito;
  String get tipoEntrega => _tipoEntrega;
  String? get sucursalRetiroId => _sucursalRetiroId;

  Future<void> cargarCarrito() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/carrito');
      _carrito = res;
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  void setTipoEntrega(String tipo, {String? sucursalId}) {
    _tipoEntrega = tipo;
    _sucursalRetiroId = sucursalId;
    notifyListeners();
  }

  Future<Map<String, dynamic>?> procesarCheckout({
    String? direccionEnvio,
    String? notas,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final body = <String, dynamic>{
        'tipo_entrega': _tipoEntrega,
        if (_tipoEntrega == 'retiro' && _sucursalRetiroId != null)
          'sucursal_id': _sucursalRetiroId,
        if (direccionEnvio != null) 'direccion_envio': direccionEnvio,
        if (notas != null) 'notas': notas,
      };

      final orden = await _apiClient.post('/checkout/ordenes', body);
      _loading = false;
      notifyListeners();
      return orden;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }
}

