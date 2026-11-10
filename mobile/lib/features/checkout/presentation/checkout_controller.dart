import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-22: Carrito y Checkout Omnicanal
class CheckoutController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _carrito;
  String _tipoEntrega = 'envio'; // 'envio' | 'retiro'
  String? _sucursalRetiroId;

  CheckoutController(this._apiClient);

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
    _tipoEntrega = tipo == 'retiro' ? 'recojo' : tipo;
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
      final tipoNormalizado = _tipoEntrega == 'retiro' ? 'recojo' : _tipoEntrega;
      final body = <String, dynamic>{
        'tipo_entrega': tipoNormalizado,
        if (tipoNormalizado == 'recojo' && _sucursalRetiroId != null)
          'sucursal_id': _sucursalRetiroId,
        'direccion_envio': ?direccionEnvio,
        'notas': ?notas,
      };

      final orden = await _apiClient.post(
        '/checkout/ordenes',
        body,
        {
          'Idempotency-Key': 'mob-chk-${DateTime.now().millisecondsSinceEpoch}',
        },
      );
      _loading = false;
      notifyListeners();
      return Map<String, dynamic>.from(orden as Map);
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }
}

