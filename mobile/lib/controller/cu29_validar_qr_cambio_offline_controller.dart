import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../core/storage/local_database.dart';

/// CU-29: Validar comprobante y procesar cambio mediante QR offline
class CU29ValidarQrCambioOfflineController extends ChangeNotifier {
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _ticketValidado;
  Map<String, dynamic>? _notaCambio;

  CU29ValidarQrCambioOfflineController(this._database);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic>? get ticketValidado => _ticketValidado;
  Map<String, dynamic>? get notaCambio => _notaCambio;

  Future<bool> escanearYValidarQr(String qrData) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final data = jsonDecode(qrData) as Map<String, dynamic>;
      final fechaStr = data['fecha_hora_local']?.toString();

      if (fechaStr != null) {
        final fechaVenta = DateTime.parse(fechaStr);
        final dias = DateTime.now().difference(fechaVenta).inDays;
        if (dias > 30) {
          _loading = false;
          _error = 'Plazo comercial de cambio expirado ($dias días transcurridos. Máximo 30 días BR-10).';
          notifyListeners();
          return false;
        }
      }

      _ticketValidado = data;
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Código QR no reconocido o firma alterada: $e';
      notifyListeners();
      return false;
    }
  }

  Future<bool> procesarCambioOffline({
    required String sucursalId,
    required String varianteDevueltaId,
    required String varianteNuevaId,
    required String motivo,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final uuid = 'cambio-off-${DateTime.now().millisecondsSinceEpoch}';
      final payload = {
        'uuid': uuid,
        'sucursal_id': sucursalId,
        'venta_origen_uuid': _ticketValidado?['uuid'],
        'variante_devuelta_id': varianteDevueltaId,
        'variante_nueva_id': varianteNuevaId,
        'motivo': motivo,
        'fecha_hora_local': DateTime.now().toIso8601String(),
        'tipo_documento': 'NOTA DE CAMBIO PRELIMINAR - PENDIENTE SYNC'
      };

      await _database.registrarOperacionOffline(
        id: uuid,
        tipo: 'cambio_offline',
        payload: payload,
        estado: 'pendiente',
      );

      _notaCambio = payload;
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Error registrando nota de cambio local: $e';
      notifyListeners();
      return false;
    }
  }
}

