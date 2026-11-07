import 'package:flutter/foundation.dart';
import '../core/storage/local_database.dart';

/// CU-28: Registrar venta de contado offline (efectivo y ticket preliminar)
class CU28VentaContadoOfflineController extends ChangeNotifier {
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _ticketPreliminar;

  CU28VentaContadoOfflineController(this._database);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic>? get ticketPreliminar => _ticketPreliminar;

  Future<Map<String, dynamic>?> registrarVentaOffline({
    required String sucursalId,
    required String usuarioId,
    required String clienteNombre,
    required String clienteDocumento,
    required List<Map<String, dynamic>> lineas,
    required double total,
    required String metodoPago,
  }) async {
    // Restricción obligatoria Sección 7.2: solo efectivo
    if (metodoPago.toLowerCase() != 'efectivo') {
      _error = 'En contingencia offline solo se admiten cobros de contado en efectivo.';
      notifyListeners();
      return null;
    }

    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final uuid = 'venta-off-${DateTime.now().millisecondsSinceEpoch}';
      final fechaLocal = DateTime.now().toIso8601String();

      final payload = {
        'uuid': uuid,
        'sucursal_id': sucursalId,
        'usuario_id': usuarioId,
        'cliente_nombre': clienteNombre.isEmpty ? 'Consumidor Final' : clienteNombre,
        'cliente_documento': clienteDocumento.isEmpty ? '0' : clienteDocumento,
        'fecha_hora_local': fechaLocal,
        'lineas': lineas,
        'total': total,
        'forma_pago': 'efectivo',
        'estado': 'pendiente',
        'leyenda_ticket': 'VENTA EN MODO OFFLINE - PENDIENTE DE SINCRONIZACIÓN'
      };

      await _database.registrarOperacionOffline(
        id: uuid,
        tipo: 'venta_offline',
        payload: payload,
        estado: 'pendiente',
      );

      _ticketPreliminar = payload;
      _loading = false;
      notifyListeners();
      return payload;
    } catch (e) {
      _loading = false;
      _error = 'Error crítico al escribir venta en almacenamiento local: $e';
      notifyListeners();
      return null;
    }
  }
}

