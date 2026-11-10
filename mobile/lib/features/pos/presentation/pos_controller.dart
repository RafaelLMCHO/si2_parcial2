import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-23: Punto de Venta (POS), Venta Rápida y Facturación
class PosController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  final List<Map<String, dynamic>> _lineas = [];
  String _metodoPago = 'efectivo'; // 'efectivo' | 'tarjeta' | 'qr'
  double _montoRecibido = 0.0;
  Map<String, dynamic>? _ultimaVenta;

  PosController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<Map<String, dynamic>> get lineas => _lineas;
  String get metodoPago => _metodoPago;
  double get montoRecibido => _montoRecibido;
  Map<String, dynamic>? get ultimaVenta => _ultimaVenta;

  double get subtotal {
    double sum = 0;
    for (var l in _lineas) {
      sum += (l['precio_unitario'] as double) * (l['cantidad'] as int);
    }
    return sum;
  }

  double get iva => subtotal * 0.13;
  double get total => subtotal + iva;
  double get cambio => (_montoRecibido >= total) ? (_montoRecibido - total) : 0.0;

  void setMetodoPago(String metodo) {
    _metodoPago = metodo;
    notifyListeners();
  }

  void setMontoRecibido(double monto) {
    _montoRecibido = monto;
    notifyListeners();
  }

  Future<bool> buscarYAgregarPorCodigo(String codigo) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/pos/variantes/barcode/$codigo');
      final existingIndex = _lineas.indexWhere((l) => l['variante_id'] == res['variante_id']);
      if (existingIndex >= 0) {
        _lineas[existingIndex]['cantidad'] = (_lineas[existingIndex]['cantidad'] as int) + 1;
      } else {
        _lineas.add({
          'variante_id': res['variante_id'],
          'sku': res['sku'],
          'prenda_nombre': res['prenda_nombre'],
          'talla': res['talla'],
          'color': res['color'],
          'precio_unitario': (res['precio_venta'] as num).toDouble(),
          'cantidad': 1,
        });
      }
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Código $codigo no encontrado en inventario';
      notifyListeners();
      return false;
    }
  }

  void actualizarCantidad(String varianteId, int delta) {
    final idx = _lineas.indexWhere((l) => l['variante_id'] == varianteId);
    if (idx >= 0) {
      final nueva = (_lineas[idx]['cantidad'] as int) + delta;
      if (nueva <= 0) {
        _lineas.removeAt(idx);
      } else {
        _lineas[idx]['cantidad'] = nueva;
      }
      notifyListeners();
    }
  }

  void limpiarVenta() {
    _lineas.clear();
    _montoRecibido = 0;
    _error = null;
    _ultimaVenta = null;
    notifyListeners();
  }

  Future<Map<String, dynamic>?> procesarCobro({
    required String sucursalId,
    String? clienteNombre,
    String? clienteDocumento,
  }) async {
    if (_lineas.isEmpty) {
      _error = 'No hay artículos en la venta';
      notifyListeners();
      return null;
    }

    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final body = {
        'idempotency_key': 'pos-${DateTime.now().millisecondsSinceEpoch}',
        'sucursal_id': sucursalId,
        'items': _lineas.map((l) => {
          'variante_id': l['variante_id'],
          'cantidad': l['cantidad'],
        }).toList(),
        'cliente': (clienteNombre != null || clienteDocumento != null)
            ? {
                'tipo': 'identificado',
                'nombre': ?clienteNombre,
                'documento': ?clienteDocumento,
              }
            : {'tipo': 'consumidor_final'},
        'pago': {
          'metodo': _metodoPago,
          'monto_recibido': _metodoPago == 'efectivo' ? _montoRecibido : total,
        },
      };

      final venta = await _apiClient.post('/pos/ventas', body);
      _ultimaVenta = venta;
      _loading = false;
      notifyListeners();
      return venta;
    } catch (e) {
      _loading = false;
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }
}

