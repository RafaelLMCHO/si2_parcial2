import 'package:flutter/foundation.dart';
import '../core/storage/local_database.dart';
import '../core/utils/uuid_helper.dart';

/// CU-26: Registrar reserva offline (generación de UUID local RFC-4122)
class CU26RegistrarReservaOfflineController extends ChangeNotifier {
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  String? _reservaUuid;

  CU26RegistrarReservaOfflineController(this._database);

  bool get loading => _loading;
  String? get error => _error;
  String? get reservaUuid => _reservaUuid;

  Future<String?> registrarReservaOffline({
    required String sucursalId,
    required DateTime fechaVisita,
    required bool probador,
    required List<Map<String, dynamic>> items,
    String? sucursalNombre,
  }) async {
    if (sucursalId.trim().isEmpty || items.isEmpty) {
      _error = 'Seleccione sucursal y al menos una prenda para reservar.';
      notifyListeners();
      return null;
    }

    _loading = true;
    _error = null;
    notifyListeners();

    try {
      // Generar UUID v4 válido para compatibilidad directa con PostgreSQL
      final uuid = generateUuidV4();
      final codigoLocal = 'RES-OFF-${uuid.substring(0, 6).toUpperCase()}';
      final payload = {
        'uuid': uuid,
        'codigo_local': codigoLocal,
        'sucursal_id': sucursalId,
        if (sucursalNombre != null && sucursalNombre.trim().isNotEmpty)
          'sucursal_nombre': sucursalNombre.trim(),
        'fecha_visita': fechaVisita.toUtc().toIso8601String(),
        'probador': probador,
        'items': items,
        'fecha_hora_local': DateTime.now().toIso8601String(),
      };

      await _database.registrarOperacionOffline(
        id: uuid,
        tipo: 'reserva_offline',
        payload: payload,
        estado: 'pendiente',
      );

      _reservaUuid = uuid;
      _loading = false;
      notifyListeners();
      return uuid;
    } catch (e) {
      _loading = false;
      _error = 'Error de almacenamiento local al guardar reserva: $e';
      notifyListeners();
      return null;
    }
  }
}

