import 'package:flutter/foundation.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/utils/uuid_helper.dart';
import '../../catalogo/data/catalogo_models.dart';
import '../../inventario/data/inventario_models.dart';

class CheckoutPagoResultado {
  const CheckoutPagoResultado({
    required this.numero,
    required this.ventaId,
    required this.totalAPagar,
    required this.ventaEstado,
    this.pagoEstado,
    this.requiereAccionExterna = false,
    this.mensaje,
  });

  final String numero;
  final String ventaId;
  final num totalAPagar;
  final String ventaEstado;
  final String? pagoEstado;
  final bool requiereAccionExterna;
  final String? mensaje;
}

/// Controlador para CU-22 y CU-24: Carrito, Checkout Omnicanal y Pasarela de Pago.
class CheckoutController extends ChangeNotifier {
  CheckoutController(this._apiClient);

  final ApiClient _apiClient;

  bool _loading = false;
  bool _submitting = false;
  String? _error;
  String? _actionError;
  String? _pendingOrderNotice;
  Map<String, dynamic>? _carrito;
  String _tipoEntrega = 'recojo'; // 'recojo' | 'envio'
  String? _sucursalRetiroId;
  String _cupon = '';
  String _direccionId = '';
  List<DisponibilidadSucursal> _sucursales = const [];
  Map<String, int> _stockPorSucursal = const {};
  Map<String, dynamic>? _validacion;
  Map<String, dynamic>? _pendingOrder;

  bool get loading => _loading;
  bool get submitting => _submitting;
  String? get error => _error;
  String? get actionError => _actionError;
  String? get pendingOrderNotice => _pendingOrderNotice;
  Map<String, dynamic>? get carrito => _carrito;
  String get tipoEntrega => _tipoEntrega;
  String? get sucursalRetiroId => _sucursalRetiroId;
  String get cupon => _cupon;
  String get direccionId => _direccionId;
  List<DisponibilidadSucursal> get sucursales => _sucursales;
  Map<String, int> get stockPorSucursal => _stockPorSucursal;
  Map<String, dynamic>? get validacion => _validacion;
  Map<String, dynamic>? get pendingOrder => _pendingOrder;

  List<dynamic> get items => (_carrito?['items'] as List<dynamic>? ?? const []);

  double get subtotalCarrito =>
      _parseNum(_carrito?['total']) ?? 0.0;

  double? _parseNum(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString().replaceAll(',', '.'));
  }

  Future<void> cargarCarrito({String empresaSlug = 'demo'}) async {
    _loading = true;
    _error = null;
    _actionError = null;
    _validacion = null;
    _pendingOrder = null;
    _pendingOrderNotice = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/carrito');
      _carrito = res is Map ? Map<String, dynamic>.from(res) : null;
      _loading = false;
      notifyListeners();

      await _cargarSucursalesDisponibles(empresaSlug, items);
      if (items.isNotEmpty && _tipoEntrega == 'recojo' && _sucursalRetiroId != null) {
        await validarCheckout(cupon: _cupon, direccionId: _direccionId, silent: true);
      }
    } catch (e) {
      _loading = false;
      _error = ApiException.fromObject(
        e,
        fallback: 'No se pudo cargar el carrito de compras.',
      ).message;
      notifyListeners();
    }
  }

  Future<void> _cargarSucursalesDisponibles(
    String empresaSlug,
    List<dynamic> cartItems,
  ) async {
    try {
      final res = await _apiClient.get(
        '/catalogo/prendas',
        queryParameters: {'empresa_slug': empresaSlug, 'limit': 50},
      );
      if (res is! Map) return;
      final listRes = PrendaListResponse.fromJson(
        Map<String, dynamic>.from(res),
      );
      if (listRes.items.isEmpty) return;

      final cartVarIds = cartItems
          .whereType<Map>()
          .map((it) => it['variante_id']?.toString() ?? '')
          .where((id) => id.isNotEmpty)
          .toSet();
      final cartSkus = cartItems
          .whereType<Map>()
          .map((it) => it['sku']?.toString() ?? '')
          .where((sku) => sku.isNotEmpty)
          .toSet();

      Prenda prendaObjetivo = listRes.items.first;
      for (final p in listRes.items) {
        final match = p.variantes.any(
          (v) => cartVarIds.contains(v.id) || cartSkus.contains(v.sku),
        );
        if (match) {
          prendaObjetivo = p;
          break;
        }
      }

      final dispRes = await _apiClient.get(
        '/inventario/prendas/${prendaObjetivo.id}/disponibilidad',
      );
      if (dispRes is! Map) return;

      final disp = DisponibilidadPrenda.fromJson(
        Map<String, dynamic>.from(dispRes),
      );
      _sucursales = disp.sucursales;

      final firstCartItem = cartItems.isNotEmpty && cartItems.first is Map
          ? Map<String, dynamic>.from(cartItems.first as Map)
          : null;
      final targetVarId = firstCartItem?['variante_id']?.toString();
      final targetSku = firstCartItem?['sku']?.toString();

      final stockMap = <String, int>{};
      for (final suc in _sucursales) {
        var stock = 0;
        if (targetVarId != null || targetSku != null) {
          for (final v in suc.variantes) {
            if (v.varianteId == targetVarId ||
                (targetSku != null && targetSku.isNotEmpty && v.sku == targetSku)) {
              stock = v.stockDisponible;
              break;
            }
          }
        } else {
          stock = suc.variantes.fold<int>(0, (s, v) => s + v.stockDisponible);
        }
        stockMap[suc.sucursalId] = stock;
      }
      _stockPorSucursal = stockMap;

      if (_sucursalRetiroId == null ||
          !_sucursales.any((s) => s.sucursalId == _sucursalRetiroId)) {
        String? preferred;
        for (final suc in _sucursales) {
          if ((_stockPorSucursal[suc.sucursalId] ?? 0) > 0) {
            preferred = suc.sucursalId;
            break;
          }
        }
        _sucursalRetiroId =
            preferred ?? (_sucursales.isNotEmpty ? _sucursales.first.sucursalId : null);
      }
      notifyListeners();
    } catch (_) {
      // Mantiene la pantalla funcional aun si falla la consulta auxiliar de sucursales.
    }
  }

  void setTipoEntrega(String tipo, {String? sucursalId}) {
    _tipoEntrega = tipo == 'retiro' ? 'recojo' : tipo;
    if (sucursalId != null) {
      _sucursalRetiroId = sucursalId;
    }
    _actionError = null;
    _validacion = null;
    _pendingOrder = null;
    _pendingOrderNotice = null;
    notifyListeners();
  }

  void setSucursalRetiro(String? sucursalId) {
    _sucursalRetiroId = sucursalId;
    _actionError = null;
    _validacion = null;
    _pendingOrder = null;
    _pendingOrderNotice = null;
    notifyListeners();
  }

  void setCupon(String value) {
    _cupon = value;
  }

  void setDireccionId(String value) {
    _direccionId = value;
  }

  Future<void> actualizarCantidadItem(String itemId, int nuevaCantidad) async {
    if (nuevaCantidad <= 0) {
      await eliminarItem(itemId);
      return;
    }

    _submitting = true;
    _actionError = null;
    _pendingOrder = null;
    _pendingOrderNotice = null;
    notifyListeners();

    try {
      final res = await _apiClient.patch('/carrito/items/$itemId', {
        'cantidad': nuevaCantidad,
      });
      if (res is Map) {
        _carrito = Map<String, dynamic>.from(res);
      }
      _validacion = null;
      _submitting = false;
      notifyListeners();
      if (items.isNotEmpty && _tipoEntrega == 'recojo' && _sucursalRetiroId != null) {
        await validarCheckout(cupon: _cupon, direccionId: _direccionId, silent: true);
      }
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo actualizar la cantidad.',
      ).message;
      notifyListeners();
    }
  }

  Future<void> eliminarItem(String itemId) async {
    _submitting = true;
    _actionError = null;
    _pendingOrder = null;
    _pendingOrderNotice = null;
    notifyListeners();

    try {
      final res = await _apiClient.delete('/carrito/items/$itemId');
      if (res is Map) {
        _carrito = Map<String, dynamic>.from(res);
      }
      _validacion = null;
      _submitting = false;
      notifyListeners();
      if (items.isNotEmpty && _tipoEntrega == 'recojo' && _sucursalRetiroId != null) {
        await validarCheckout(cupon: _cupon, direccionId: _direccionId, silent: true);
      }
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo eliminar la prenda del carrito.',
      ).message;
      notifyListeners();
    }
  }

  Future<bool> validarCheckout({
    String? cupon,
    String? direccionId,
    bool silent = false,
  }) async {
    if (cupon != null) _cupon = cupon;
    if (direccionId != null) _direccionId = direccionId;

    final tipoNormalizado = _tipoEntrega == 'retiro' ? 'recojo' : _tipoEntrega;
    final cleanCupon = _cupon.trim();
    final cleanDir = _direccionId.trim();

    if (tipoNormalizado == 'recojo' &&
        (_sucursalRetiroId == null || _sucursalRetiroId!.isEmpty)) {
      if (!silent) {
        _actionError = 'Seleccione una sucursal de recojo para validar el stock.';
        notifyListeners();
      }
      return false;
    }

    if (tipoNormalizado == 'envio' && cleanDir.isEmpty) {
      _validacion = null;
      if (!silent) {
        _actionError =
            'El envío a domicilio requiere el UUID de una dirección registrada. Use "Recojo en sucursal física (Gratis)" para continuar.';
        notifyListeners();
      }
      return false;
    }

    if (!silent) {
      _submitting = true;
      _actionError = null;
      notifyListeners();
    }

    try {
      final body = <String, dynamic>{
        'tipo_entrega': tipoNormalizado,
        if (tipoNormalizado == 'recojo') 'sucursal_id': _sucursalRetiroId,
        if (tipoNormalizado == 'envio') 'direccion_id': cleanDir,
        if (cleanCupon.isNotEmpty) 'cupon': cleanCupon,
      };
      final res = await _apiClient.post('/checkout/validar', body);
      _validacion = res is Map ? Map<String, dynamic>.from(res) : null;
      _submitting = false;
      notifyListeners();
      return true;
    } catch (e) {
      _submitting = false;
      if (!silent) {
        _actionError = ApiException.fromObject(
          e,
          fallback: 'No se pudo validar el checkout.',
        ).message;
      }
      notifyListeners();
      return false;
    }
  }

  Future<CheckoutPagoResultado?> realizarPago({
    String? cupon,
    String? direccionId,
  }) async {
    if (cupon != null) _cupon = cupon;
    if (direccionId != null) _direccionId = direccionId;

    if (items.isEmpty) {
      _actionError = 'El carrito de compras está vacío.';
      notifyListeners();
      return null;
    }

    final tipoNormalizado = _tipoEntrega == 'retiro' ? 'recojo' : _tipoEntrega;
    final cleanCupon = _cupon.trim();
    final cleanDir = _direccionId.trim();

    if (tipoNormalizado == 'recojo' &&
        (_sucursalRetiroId == null || _sucursalRetiroId!.isEmpty)) {
      _actionError = 'Seleccione una sucursal física para el recojo.';
      notifyListeners();
      return null;
    }

    if (tipoNormalizado == 'envio' && cleanDir.isEmpty) {
      _actionError =
          'El envío a domicilio requiere el UUID de una dirección registrada. Seleccione "Recojo en sucursal física (Gratis)".';
      notifyListeners();
      return null;
    }

    _submitting = true;
    _actionError = null;
    _pendingOrderNotice = null;
    notifyListeners();

    try {
      if (_pendingOrder == null) {
        if (_validacion == null) {
          await validarCheckout(
            cupon: cleanCupon,
            direccionId: cleanDir,
            silent: true,
          );
        }
        final faltantes = (_validacion?['lineas_faltantes'] as List<dynamic>? ?? const []);
        if (faltantes.isNotEmpty) {
          _submitting = false;
          _actionError =
              'No hay stock suficiente en la sucursal seleccionada para todas las prendas del carrito. Cambia de sucursal o ajusta la cantidad.';
          notifyListeners();
          return null;
        }

        final ordenRes = await _apiClient.post(
          '/checkout/ordenes',
          {
            'tipo_entrega': tipoNormalizado,
            if (tipoNormalizado == 'recojo') 'sucursal_id': _sucursalRetiroId,
            if (tipoNormalizado == 'envio') 'direccion_id': cleanDir,
            if (cleanCupon.isNotEmpty) 'cupon': cleanCupon,
          },
          {'Idempotency-Key': generateUuidV4()},
        );
        _pendingOrder = Map<String, dynamic>.from(ordenRes as Map);
      } else if (_pendingOrder!['estado'] == 'pago_fallido') {
        final ventaIdPrev = _pendingOrder!['venta_id'].toString();
        final retryRes = await _apiClient.post(
          '/checkout/ordenes/$ventaIdPrev/reintentar-pago',
          {},
        );
        _pendingOrder = Map<String, dynamic>.from(retryRes as Map);
      }

      final ventaId = _pendingOrder!['venta_id'].toString();
      final numero = _pendingOrder!['numero']?.toString() ?? '-';
      final totalAPagar =
          _parseNum(_pendingOrder!['total_a_pagar']) ?? subtotalCarrito;

      Map<String, dynamic> intentMap;
      try {
        final intentRes = await _apiClient.post(
          '/pagos/intencion',
          {'venta_id': ventaId},
          {'Idempotency-Key': generateUuidV4()},
        );
        intentMap = Map<String, dynamic>.from(intentRes as Map);
      } catch (e) {
        final apiErr = ApiException.fromObject(
          e,
          fallback: 'No se pudo iniciar la intención de pago.',
        );
        _submitting = false;
        if (apiErr.statusCode == 503 || apiErr.code == 'PASARELA_NO_CONFIGURADA') {
          _pendingOrderNotice =
              'Se registró tu orden $numero (pendiente de pago), pero el servidor aún no tiene configurada la pasarela Stripe (STRIPE_SECRET_KEY / STRIPE_ALLOW_MOCK). Cuando se habilite podrás reintentar sin duplicar la orden.';
        } else {
          _pendingOrderNotice =
              'Orden $numero creada en estado pendiente de pago. Error al contactar la pasarela: ${apiErr.message}';
        }
        _actionError = apiErr.message;
        notifyListeners();
        return null;
      }

      final pagoId = intentMap['pago_id']?.toString() ?? '';
      if (pagoId.isEmpty) {
        _submitting = false;
        _pendingOrderNotice =
            'Orden $numero creada, pero no se recibió identificador de pago de la pasarela.';
        _actionError = _pendingOrderNotice;
        notifyListeners();
        return null;
      }

      try {
        final conciliarRes = await _apiClient.post(
          '/pagos/$pagoId/conciliar',
          {},
          null,
          {'payment_method': 'pm_card_visa'},
        );
        final estadoMap = Map<String, dynamic>.from(conciliarRes as Map);
        final ventaEstado = estadoMap['venta_estado']?.toString() ?? '';
        final pagoEstado = estadoMap['pago_estado']?.toString();

        _submitting = false;

        if (ventaEstado == 'completada' || pagoEstado == 'completado') {
          _pendingOrder = null;
          _pendingOrderNotice = null;
          _validacion = null;
          notifyListeners();
          return CheckoutPagoResultado(
            numero: numero,
            ventaId: ventaId,
            totalAPagar: totalAPagar,
            ventaEstado: ventaEstado,
            pagoEstado: pagoEstado,
          );
        }

        final mensaje = estadoMap['mensaje_error']?.toString() ??
            'Pago pendiente de confirmación ($pagoEstado).';
        _pendingOrderNotice = 'Orden $numero registrada. $mensaje';
        notifyListeners();
        return CheckoutPagoResultado(
          numero: numero,
          ventaId: ventaId,
          totalAPagar: totalAPagar,
          ventaEstado: ventaEstado,
          pagoEstado: pagoEstado,
          requiereAccionExterna: true,
          mensaje: mensaje,
        );
      } catch (e) {
        final apiErr = ApiException.fromObject(
          e,
          fallback: 'No se pudo confirmar el cobro con la pasarela.',
        );
        _submitting = false;
        _pendingOrderNotice =
            'Orden $numero e intención de pago ($pagoId) creadas. No se pudo confirmar el cobro automático: ${apiErr.message}';
        _actionError = apiErr.message;
        notifyListeners();
        return null;
      }
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'Error al procesar el checkout.',
      ).message;
      notifyListeners();
      return null;
    }
  }
}
