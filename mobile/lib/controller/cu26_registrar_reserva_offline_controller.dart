import 'package:flutter/foundation.dart';
import '../core/storage/local_database.dart';

/// CU-26: Registrar reserva offline (generación de UUID local)
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
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      // Generar UUID v4 local
      final uuid = 'res-off-${DateTime.now().millisecondsSinceEpoch}-${items.length}';
      final payload = {
        'uuid': uuid,
        'sucursal_id': sucursalId,
        'fecha_visita': fechaVisita.toIso8601String(),
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

